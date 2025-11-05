# Copyright (c) 2021 SUSE LLC
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of version 3 of the GNU General Public License as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.   See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, contact SUSE LLC.
#
# To contact SUSE about this file by physical or electronic mail,
# you may find current contact information at www.suse.com

import pytest


pytest_plugins = [
    'harvester_e2e_tests.fixtures.api_client',
    'harvester_e2e_tests.fixtures.rancher_api_client',
    'harvester_e2e_tests.fixtures.images',
    'harvester_e2e_tests.fixtures.networks',
    'harvester_e2e_tests.fixtures.rancher',
]

# This is not really a test case as such, but rather a gate to prevent the rest
# of the test suite to run when Rancher is not ready yet.
# The problem is that Rancher may service API requests when the webhook
# deployment has not yet an available Pod to service requests. This may result
# in some fields like `creatorId` being left unpopulated and produce other
# errors down the line.
@pytest.mark.dependency(name="wait_for_rancher", scope="session")
def test_wait_for_rancher(rancher_api_client, polling_for, polling_for_any):
    polling_for(
        "waiting for rancher deployment to get ready",
        lambda code, data, ready: bool(ready),
        rancher_api_client.cluster_deployments.ready,
            'local', ['cattle-system/rancher', 'cattle-system/rancher-webhook'],
        timeout=300
    )

    polling_for_any(
        "waiting for CAPI controller",
        lambda code, data, ready: bool(ready),
        rancher_api_client.cluster_deployments.ready,
            'local', ['cattle-provisioning-capi-system/capi-controller-manager',
                      'cattle-turtles-system/rancher-turtles-controller-manager'],
        timeout=300
    )


@pytest.mark.p0
@pytest.mark.rancher
@pytest.mark.dependency(name="import_harvester", scope="session", depends=["wait_for_rancher"])
def test_import_harvester(api_client, rancher_api_client, harvester_mgmt_cluster, polling_for):
    # Get cluster registration URL in Rancher's Virtualization Management
    code, data = polling_for(
        f"registration URL for the imported harvester {harvester_mgmt_cluster['name']}",
        lambda code, data: 200 == code and data.get('manifestUrl'),
        rancher_api_client.cluster_registration_tokens.get, harvester_mgmt_cluster['id']
    )

    # Set cluster-registration-url on Harvester
    updates = dict(value=data['manifestUrl'])
    code, data = api_client.settings.update("cluster-registration-url", updates)
    assert 200 == code, (
        f"Failed to update Harvester's settings `cluster-registration-url`"
        f" with error: {code}, {data}"
    )

    # Check Cluster becomes `active` in Rancher's Virtualization Management
    polling_for(
        "harvester to be ready",
        lambda code, data:
            "active" == data['metadata']['state']['name'] and
            "Ready" in data['metadata']['state']['message'],
        rancher_api_client.mgmt_clusters.get, harvester_mgmt_cluster['name']
    )


@pytest.mark.p1
@pytest.mark.rancher
@pytest.mark.dependency(depends=["import_harvester"])
def test_add_project_owner_user(api_client, rancher_api_client, unique_name, wait_timeout,
                                harvester_mgmt_cluster, polling_for):
    cluster_id = harvester_mgmt_cluster['id']
    username, password = f"owner-{unique_name}", unique_name

    spec = rancher_api_client.users.Spec(password)
    # create user
    code, data = rancher_api_client.users.create(username, spec)
    assert 201 == code, (
        f"Failed to create user {username!r}\n"
        f"API Status({code}): {data}"
    )
    uid, upids = data['id'], data['principalIds']

    # add role `user` to user
    code, data = rancher_api_client.users.add_role(uid, 'user')
    assert 201 == code, (
        f"Failed to add role 'user' for user {username!r}\n"
        f"API Status({code}): {data}"
    )

    # Get `Default` project's uid
    cluster_api = rancher_api_client.clusters.explore(cluster_id)
    code, data = cluster_api.projects.get_by_name('Default')
    assert 200 == code, (code, data)
    project_id = data['id']
    # add user to `Default` project as *project-owner*
    code, data = cluster_api.project_members.create(project_id, upids[0], "project-owner")
    assert 201 == code, (code, data)
    proj_muid = data['id']

    # Login as the user
    endpoint = rancher_api_client.endpoint
    user_rapi = rancher_api_client.login(endpoint, username, password, ssl_verify=False)
    user_capi = user_rapi.clusters.explore(cluster_id)
    # Check user can only view the project he joined
    code, data = user_capi.projects.get()
    assert 200 == code, (code, data)
    assert 1 == len(data['data']), (code, data)

    # teardown
    cluster_api.project_members.delete(proj_muid)
    rancher_api_client.users.delete(uid)

    polling_for(
        f"user {username} to be deleted",
        lambda code, data: 404 == code,
        rancher_api_client.users.get, uid
    )

@pytest.mark.p1
@pytest.mark.rancher
@pytest.mark.dependency(depends=["import_harvester"])
def test_add_project_member_user(api_client, rancher_api_client, unique_name, wait_timeout,
                                 harvester_mgmt_cluster, polling_for):
    cluster_id = harvester_mgmt_cluster['id']
    username, password = f"member-{unique_name}", unique_name

    spec = rancher_api_client.users.Spec(password)
    # create user
    code, data = rancher_api_client.users.create(username, spec)
    assert 201 == code, (
        f"Failed to create user {username!r}\n"
        f"API Status({code}): {data}"
    )
    uid, upids = data['id'], data['principalIds']

    # add role `user` to user
    code, data = rancher_api_client.users.add_role(uid, 'user')
    assert 201 == code, (
        f"Failed to add role 'user' for user {username!r}\n"
        f"API Status({code}): {data}"
    )

    # Get `Default` project's uid
    cluster_api = rancher_api_client.clusters.explore(cluster_id)
    code, data = cluster_api.projects.get_by_name('Default')
    assert 200 == code, (code, data)
    project_id = data['id']
    # add user to `Default` project as *project-member*
    code, data = cluster_api.project_members.create(project_id, upids[0], "project-member")
    assert 201 == code, (code, data)
    proj_muid = data['id']

    # Login as the user
    endpoint = rancher_api_client.endpoint
    user_rapi = rancher_api_client.login(endpoint, username, password, ssl_verify=False)
    user_capi = user_rapi.clusters.explore(cluster_id)
    # Check user can only view the project he joined
    code, data = user_capi.projects.get()
    assert 200 == code, (code, data)
    assert 1 == len(data['data']), (code, data)

    # teardown
    cluster_api.project_members.delete(proj_muid)
    rancher_api_client.users.delete(uid)

    polling_for(
        f"user {username} to be deleted",
        lambda code, data: 404 == code,
        rancher_api_client.users.get, uid
    )
