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

#
# To contact SUSE about this file by physical or electronic mail,
# you may find current contact information at www.suse.com

import pytest


pytest_plugins = [
    'harvester_e2e_tests.fixtures.api_client',
    'harvester_e2e_tests.fixtures.rancher_api_client',
    'harvester_e2e_tests.fixtures.images',
    'harvester_e2e_tests.fixtures.networks',
]


@pytest.fixture(scope='class')
def rke1_node_template(rancher_api_client, unique_name, ubuntu_image,
                       vlan_network, harvester_cloud_credential):
    code, data = rancher_api_client.node_templates.create(
        name=unique_name,
        cpus=2,
        mems=4,
        disks=40,
        image_id=ubuntu_image['id'],
        network_id=vlan_network['name'],
        ssh_user=ubuntu_image['ssh_user'],
        cloud_credential_id=harvester_cloud_credential['id'],
        user_data=(
            "#cloud-config\n"
            "password: test\n"
            "chpasswd:\n"
            "    expire: false\n"
            "ssh_pwauth: true\n"
        ),
    )
    assert 201 == code, (
        f"Failed to create NodeTemplate {unique_name} with error: {code}, {data}"
    )

    template_id = data['id']

    yield data

    import time
    time.sleep(30)  # need to wait until nodes are deleted
    code, data = rancher_api_client.node_templates.delete(name=template_id)
    assert 204 == code, (
        f"Failed to delete NodeTemplate {unique_name} with error: {code}, {data}"
    )


@pytest.mark.p1
@pytest.mark.rancher
@pytest.mark.rke1
@pytest.mark.usefixtures("rke1_cluster", "rke1_node_template")
class TestRKE1:
    @pytest.mark.dependency(
        depends=["import_harvester"],
        scope="session",
        name="create_rke1"
    )
    def test_create_rke1(self, rancher_api_client, unique_name, harvester_mgmt_cluster,
                         rancher_wait_timeout,
                         rke1_cluster,
                         rke1_node_template, polling_for):
        code, data = rancher_api_client.kube_configs.create(
            rke1_cluster['name'],
            harvester_mgmt_cluster['id']
        )
        assert 200 == code, f"Failed to create harvester kubeconfig with error: {code}, {data}"
        assert data.strip(), f"Harvester kubeconfig should not be empty: {code}, {data}"
        kubeconfig = data

        node_template_id = rke1_node_template['id']

        code, data = rancher_api_client.clusters.create(
            rke1_cluster['name'], rke1_cluster['k8s_version'], kubeconfig
        )
        assert 201 == code, (
            f"Failed to create cluster {rke1_cluster['name']} with error: {code}, {data}"
        )

        # update fixture value
        rke1_cluster['id'] = data['id']

        # check cluster created and ready for use
        polling_for(
            f"cluster {rke1_cluster['name']} to be ready",
            lambda code, data:
                200 == code and
                "RKESecretsMigrated" in [c['type'] for c in data['conditions']],
            rancher_api_client.clusters.get, rke1_cluster['id'],
            timeout=rancher_wait_timeout
        )

        code, data = rancher_api_client.node_pools.create(
            cluster_id=rke1_cluster['id'],
            node_template_id=node_template_id,
            hostname_prefix=f"{rke1_cluster['name']}-",
            quantity=rke1_cluster['machine_count']
        )
        assert 201 == code, (
            f"Failed to create NodePools for cluster {rke1_cluster['name']}\n"
            f"API Status({code}): {data}"
        )

        polling_for(
            f"MgmtCluster {rke1_cluster['name']} to be ready",
            lambda code, data: code == 200 and data.get('status', {}).get('ready', False),
            rancher_api_client.mgmt_clusters.get, rke1_cluster['id'],
            timeout=rancher_wait_timeout
        )

    @pytest.mark.dependency(depends=["create_rke1"])
    def test_create_pvc(self, rancher_api_client, harvester_mgmt_cluster,
                        unique_name, polling_for):
        cluster_id = harvester_mgmt_cluster['id']
        capi = rancher_api_client.clusters.explore(cluster_id)

        # Create PVC
        size = "1Gi"
        spec = capi.pvcs.Spec(size)
        code, data = capi.pvcs.create(unique_name, spec)
        assert 201 == code, (code, data)

        # Verify PVC is created
        code, data = polling_for(
            f"PVC {unique_name} to be in Bound phase",
            lambda code, data: "Bound" == data['status'].get('phase'),
            capi.pvcs.get, unique_name
        )

        # Verify the PV for created PVC
        pv_code, pv_data = capi.pvs.get(data['spec']['volumeName'])
        assert 200 == pv_code, (
            f"Relevant PV is NOT available for created PVC's PV({data['spec']['volumeName']})\n"
            f"Response data of PV: {data}"
        )

        # Verify size of the PV is aligned to requested size of PVC
        assert size == pv_data['spec']['capacity']['storage'], (
            "Size of the PV is NOT aligned to requested size of PVC,"
            f" expected: {size}, PV's size: {pv_data['spec']['capacity']['storage']}\n"
            f"Response data of PV: {data}"
        )

        # Verify PVC's size
        created_spec = capi.pvcs.Spec.from_dict(data)
        assert size == spec.size, (
            f"Size is NOT correct in created PVC, expected: {size}, created: {spec.size}\n"
            f"Response data: {data}"
        )

        # Verify the storage class exists
        sc_code, sc_data = capi.scs.get(created_spec.storage_cls)
        assert 200 == sc_code, (
            f"Storage Class is NOT exists for created PVC\n"
            f"Created PVC Spec: {data}\n"
            f"SC Status({sc_code}): {sc_data}"
        )

        # verify the storage class is marked `default`
        assert 'true' == sc_data['metadata']['annotations'][capi.scs.DEFAULT_KEY], (
            f"Storage Class is NOT the DEFAULT for created PVC\n"
            f"Requested Storage Class: {spec.storage_cls!r}"
            f"Created PVC Spec: {data}\n"
            f"SC Status({sc_code}): {sc_data}"
        )

        # teardown
        capi.pvcs.delete(unique_name)

    # harvester-cloud-provider
    @pytest.mark.dependency(depends=["create_rke1"], name="cloud_provider_chart")
    def test_cloud_provider_chart(self, rancher_api_client, rke1_cluster, polling_for):
        chart = "harvester-cloud-provider"
        deployment = "harvester-cloud-provider"

        # Wait for clusterrepo to finish downloading
        polling_for(
            f"cluster repo downloading",
            lambda code, data:
                200 == code and len(data.get('status', {}).get('conditions', [])) > 1,
                rancher_api_client.cluster_repos.get,
                    rke1_cluster['id'], 'rancher-charts',
            timeout=180
        )

        chart_data = rancher_api_client.charts.data(rke1_cluster['id'], 'kube-system', chart)
        chart_data['charts'][0]['values']['cloudConfigPath'] = "/etc/kubernetes/cloud-config"

        polling_for(
            f"chart {chart} to be create",
            lambda code, data:
                201 == code,
            rancher_api_client.charts.create_with_data,
                rke1_cluster['id'], chart_data,
            timeout=60
        )
        # Polling on creation for possible 500 error in Rancher Apps
        # * https://github.com/rancher/rancher/issues/37610
        # * https://github.com/rancher/rancher/issues/43036

        polling_for(
            f"chart {chart} to be ready",
            lambda code, data:
                200 == code and
                "deployed" == data.get("metadata", {}).get("state", {}).get("name"),
            rancher_api_client.charts.get,
                rke1_cluster['id'], "kube-system", chart
        )
        polling_for(
            f"deployment {deployment} to be ready",
            lambda code, data:
                200 == code and
                "active" == data.get("metadata", {}).get("state", {}).get("name"),
            rancher_api_client.cluster_deployments.get,
                rke1_cluster['id'], "kube-system", deployment
        )

    @pytest.mark.dependency(depends=["cloud_provider_chart"], name="deploy_nginx")
    def test_deploy_nginx(self, rancher_api_client, rke1_cluster, nginx_deployment, polling_for):
        code, data = rancher_api_client.cluster_deployments.create(
            rke1_cluster['id'], nginx_deployment['namespace'],
            nginx_deployment['name'], nginx_deployment['image']
        )
        assert 201 == code, (
            f"Fail to deploy {nginx_deployment['name']} on {rke1_cluster['name']}\n"
            f"API Response: {code}, {data}"
        )

        polling_for(
            f"deployment {nginx_deployment['name']} to be ready",
            lambda code, data:
                200 == code and
                "active" == data.get("metadata", {}).get("state", {}).get("name"),
            rancher_api_client.cluster_deployments.get,
                rke1_cluster['id'], nginx_deployment['namespace'], nginx_deployment['name']
        )

    @pytest.mark.dependency(depends=["deploy_nginx"])
    def test_load_balancer_service(self, rancher_api_client, rke1_cluster, nginx_deployment,
                                   lb_service, polling_for):
        # create LB service
        code, data = rancher_api_client.cluster_services.create(
            rke1_cluster['id'], lb_service["data"]
        )
        assert 201 == code, (
            f"Fail to create {lb_service['name']} for {nginx_deployment['name']}\n"
            f"API Response: {code}, {data}"
        )

        # check service active
        code, data = polling_for(
            f"service {lb_service['name']} to be ready",
            lambda code, data:
                200 == code and
                "active" == data.get("metadata", {}).get("state", {}).get("name"),
            rancher_api_client.cluster_services.get, rke1_cluster['id'], lb_service['name']
        )

        # check Nginx can be queired via LB
        try:
            ingress_ip = data["status"]["loadBalancer"]["ingress"][0]['ip']
            ingress_port = data['spec']['ports'][0]['port']
            ingress_url = f"http://{ingress_ip}:{ingress_port}"
        except Exception as e:
            raise AssertionError(
                f"Fail to get ingress info from {lb_service['name']}\n"
                f"Got error: {e}\n"
                f"Service data: {data}"
            )
        resp = rancher_api_client.session.get(ingress_url)
        assert resp.ok and "Welcome to nginx" in resp.text, (
            f"Fail to query load balancer {lb_service['name']}\n"
            f"Got error: {resp.status_code}, {resp.text}\n"
            f"Service data: {data}"
        )

        # teardown
        rancher_api_client.cluster_services.delete(rke1_cluster['id'], lb_service["name"])

    # harvester-csi-driver
    @pytest.mark.dependency(depends=["create_rke1"], name="csi_driver_chart")
    def test_csi_driver_chart(self, rancher_api_client, rke1_cluster, polling_for):
        chart, deployment = "harvester-csi-driver", "harvester-csi-driver-controllers"
        polling_for(
            f"chart {chart} to be create",
            lambda code, data:
                201 == code,
            rancher_api_client.charts.create,
                rke1_cluster['id'], "kube-system", chart,
            timeout=60
        )
        # Polling on creation for possible 500 error in Rancher Apps
        # * https://github.com/rancher/rancher/issues/37610
        # * https://github.com/rancher/rancher/issues/43036

        polling_for(
            f"chart {chart} to be ready",
            lambda code, data:
                200 == code and
                "deployed" == data.get("metadata", {}).get("state", {}).get("name"),
            rancher_api_client.charts.get,
                rke1_cluster['id'], "kube-system", chart
        )
        polling_for(
            f"deployment {deployment} to be ready",
            lambda code, data:
                200 == code and
                "active" == data.get("metadata", {}).get("state", {}).get("name"),
            rancher_api_client.cluster_deployments.get,
                rke1_cluster['id'], "kube-system", deployment
        )

    @pytest.mark.dependency(depends=["csi_driver_chart"], name="csi_deployment")
    def test_csi_deployment(self, rancher_api_client, rke1_cluster, csi_deployment, polling_for):
        # create pvc
        code, data = rancher_api_client.pvcs.create(rke1_cluster['id'], csi_deployment['pvc'])
        assert 201 == code, (
            f"Fail to create {csi_deployment['pvc']} on {rke1_cluster['name']}\n"
            f"API Response: {code}, {data}"
        )

        polling_for(
            f"PVC {csi_deployment['pvc']} to be ready",
            lambda code, data:
                200 == code and
                "bound" == data.get("metadata", {}).get("state", {}).get("name"),
            rancher_api_client.pvcs.get, rke1_cluster['id'], csi_deployment['pvc']
        )

        # deployment with csi
        code, data = rancher_api_client.cluster_deployments.create(
            rke1_cluster['id'], csi_deployment['namespace'],
            csi_deployment['name'], csi_deployment['image'], csi_deployment['pvc']
        )
        assert 201 == code, (
            f"Fail to deploy {csi_deployment['name']} on {rke1_cluster['name']}\n"
            f"API Response: {code}, {data}"
        )

        polling_for(
            f"deployment {csi_deployment['name']} to be ready",
            lambda code, data:
                200 == code and
                "active" == data.get("metadata", {}).get("state", {}).get("name"),
            rancher_api_client.cluster_deployments.get,
                rke1_cluster['id'], csi_deployment['namespace'], csi_deployment['name']
        )

    @pytest.mark.dependency(depends=["csi_deployment"])
    def test_delete_deployment(self, rancher_api_client, rke1_cluster, csi_deployment,
                               polling_for):
        code, data = rancher_api_client.cluster_deployments.delete(
            rke1_cluster['id'], csi_deployment['namespace'], csi_deployment['name']
        )
        assert 204 == code, (
            f"Failed to delete deployment {csi_deployment['name']} with error: {code}, {data}"
        )

        polling_for(
            f"deployment {csi_deployment['name']} to be deleted",
            lambda code, data:
                code == 404,
            rancher_api_client.cluster_deployments.get,
                rke1_cluster['id'], csi_deployment['namespace'], csi_deployment['name']
        )

        # teardown
        rancher_api_client.pvcs.delete(rke1_cluster['id'], csi_deployment['pvc'])

    @pytest.mark.dependency(depends=["create_rke1"])
    def test_delete_rke1(self, api_client, rancher_api_client, rke1_cluster,
                         rancher_wait_timeout, polling_for):
        code, data = rancher_api_client.mgmt_clusters.delete(rke1_cluster['id'])
        assert 200 == code, (
            f"Failed to delete RKE2 MgmtCluster {rke1_cluster['name']} with error: {code}, {data}"
        )

        def _remaining_vm_cnt() -> int:
            # in RKE1, when the cluster is deleted, VMs may still in Terminating status
            code, data = api_client.vms.get()
            remaining_vm_cnt = 0
            for d in data.get('data', []):
                vm_name = d.get('metadata', {}).get('name', "")
                if vm_name.startswith(f"{rke1_cluster['name']}-"):
                    remaining_vm_cnt += 1
            return remaining_vm_cnt

        polling_for(
            f"cluster {rke1_cluster['name']} to be deleted",
            lambda code, data: code == 404 and _remaining_vm_cnt() == 0,
            rancher_api_client.clusters.get, rke1_cluster['id'],
            timeout=rancher_wait_timeout
        )
