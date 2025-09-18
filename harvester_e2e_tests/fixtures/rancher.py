# Miscellaneous fixtures for Rancher integration tests

import pytest


pytest_plugins = [
    'harvester_e2e_tests.fixtures.rancher_api_client',
]


@pytest.fixture(scope="module",
                params=[1,
                        pytest.param(3, marks=pytest.mark.skip(reason="Skip for low I/O env."))])
def machine_count(request):
    return request.param


@pytest.fixture(scope='class')
def rke1_cluster(unique_name, rancher_api_client, machine_count, rke1_version):
    name = f"rke1-{unique_name}-{machine_count}"
    yield {
        "name": name,
        "id": "",    # set in Test_RKE1::test_create_rke1, e.g. c-m-n6bsktxb
        "machine_count": machine_count,
        "k8s_version": rke1_version
    }

    rancher_api_client.mgmt_clusters.delete(name)


@pytest.fixture(scope='class')
def rke2_cluster(unique_name, rancher_api_client, machine_count, rke2_version):
    name = f"rke2-{unique_name}-{machine_count}"
    yield {
        "name": name,
        "id": "",    # set in Test_RKE2::test_create_rke2, e.g. c-m-n6bsktxb
        "machine_count": machine_count,
        "k8s_version": rke2_version
    }

    rancher_api_client.mgmt_clusters.delete(name)


@pytest.fixture(scope='class')
def k3s_cluster(unique_name, rancher_api_client, machine_count, k3s_version):
    yield {
        "name": f"k3s-{unique_name}-{machine_count}",
        "id": "",  # set in Test_K3s::test_create_k3s
        "machine_count": machine_count,
        "k8s_version": k3s_version
    }


@pytest.fixture(scope='module')
def rancher_machine_config(rancher_api_client, unique_name, ubuntu_image,
                           vlan_network):
    code, data = rancher_api_client.harvester_configs.create(
        name=f"machine-config-{unique_name}",
        cpus="4",
        mems="8",
        disks="60",
        image_id=ubuntu_image['id'],
        network_id=vlan_network['name'],
        ssh_user=ubuntu_image['ssh_user'],
        user_data=(
            "#cloud-config\n"
            "password: test\n"
            "chpasswd:\n"
            "    expire: false\n"
            "ssh_pwauth: true\n"
        ),
    )
    assert 201 == code, (
        f"Failed to create machine config with error: {code}, {data}"
    )

    yield data


@pytest.fixture(scope='session')
def harvester_mgmt_cluster(api_client, rancher_api_client, unique_name, polling_for):
    """ Rancher creates Harvester entry (Import Existing)
    """
    cluster_name = f"harvester-{unique_name}"

    code, data = rancher_api_client.mgmt_clusters.create_harvester(cluster_name)
    assert 201 == code, (
         f"Failed to create Harvester entry {cluster_name} with error: {code}, {data}"
    )

    code, data = polling_for(
        f"finding clusterName in MgmtCluster {cluster_name}",
        lambda code, data: data.get('status', {}).get('clusterName'),
        rancher_api_client.mgmt_clusters.get, cluster_name
    )

    yield {
        "name": cluster_name,
        "id": data['status']['clusterName']     # e.g. c-m-n6bsktxb
    }

    rancher_api_client.mgmt_clusters.delete(cluster_name)
    updates = dict(value="")
    api_client.settings.update("cluster-registration-url", updates)


@pytest.fixture(scope='module')
def harvester_ui_extension(rancher_api_client):
    pass


@pytest.fixture(scope='session')
def harvester_cloud_credential(api_client, rancher_api_client,
                               harvester_mgmt_cluster, unique_name):
    code, data = rancher_api_client.clusters.generate_kubeconfig(
        harvester_mgmt_cluster['id']
    )
    assert 200 == code, (
        f"Failed to create kubconfig with error: {code}, {data}"
    )
    harvester_kubeconfig = data['config']

    code, data = rancher_api_client.cloud_credentials.create(
        unique_name,
        harvester_kubeconfig,
        harvester_mgmt_cluster['id']
    )
    assert 201 == code, (
        f"Failed to create cloud credential with error: {code}, {data}"
    )
    name = data['id']

    code, data = rancher_api_client.cloud_credentials.get(name)
    assert 200 == code, (
        f"Failed to get cloud credential {unique_name} with error: {code}, {data}"
    )

    yield data

    rancher_api_client.cloud_credentials.delete(name)


@pytest.fixture(scope='session')
def nginx_container_image():
    yield "registry.opensuse.org/opensuse/nginx:latest"


@pytest.fixture(scope='session')
def csi_deployment(unique_name, nginx_container_image):
    yield {
        "namespace": "default",
        "name": f"csi-{unique_name}",
        "image": nginx_container_image,
        "pvc": f"pvc-{unique_name}"
    }


@pytest.fixture(scope='session')
def nginx_deployment(unique_name, nginx_container_image):
    return {
        "namespace": "default",
        "name": f"nginx-{unique_name}",
        "image": nginx_container_image
    }
