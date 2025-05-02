import json

import pytest
from .base import wait_until


@pytest.fixture(scope="session")
def vlan_id(request):
    vlan_id = request.config.getoption('--vlan-id')
    assert 0 < vlan_id < 4095, f"VLAN ID should be in range 1-4094, not {vlan_id}"
    return vlan_id


@pytest.fixture(scope="session")
def vlan_nic(request):
    vlan_nic = request.config.getoption('--vlan-nic')
    assert vlan_nic, f"VLAN NIC {vlan_nic} not configured correctly."
    return vlan_nic


@pytest.fixture(scope="session")
def network_checker(api_client, wait_timeout, sleep_timeout):
    class NetworkChecker:
        def __init__(self):
            self.networks = api_client.networks

        @wait_until(wait_timeout, sleep_timeout)
        def wait_routed(self, vnet_name):
            code, data = self.networks.get(vnet_name)
            annotations = data['metadata'].get('annotations', {})
            route = json.loads(annotations.get('network.harvesterhci.io/route', '{}'))
            if code == 200 and route.get('connectivity') == 'true':
                return True, (code, data)
            return False, (code, data)

    return NetworkChecker()


@pytest.fixture(scope='module')
def vlan_network(request, api_client, vlan_id, vlan_nic):
    api_client.clusternetworks.create(vlan_nic)
    api_client.clusternetworks.create_config(vlan_nic, vlan_nic, vlan_nic)

    network_name = f'vlan-network-{vlan_id}'
    code, data = api_client.networks.get(network_name)
    if code != 200:
        code, data = api_client.networks.create(network_name, vlan_id, cluster_network=vlan_nic)
        assert 201 == code, (
            f"Failed to create network-attachment-definition {network_name} \
                with error {code}, {data}"
        )
    namespace = data['metadata']['namespace']
    name = data['metadata']['name']

    yield {
        "name": name,
        "id": f"{namespace}/{name}"
    }

    api_client.networks.delete(network_name)


@pytest.fixture(scope="module")
def ip_pool(request, api_client, unique_name, vlan_network):
    name = f"ippool-{unique_name}"
    ip_pool_subnet = request.config.getoption('--ip-pool-subnet')
    ip_pool_start = request.config.getoption('--ip-pool-start')
    ip_pool_end = request.config.getoption('--ip-pool-end')

    code, data = api_client.ippools.create(
        name, ip_pool_subnet, ip_pool_start, ip_pool_end, vlan_network["id"]
    )
    assert 201 == code, (
        f"Failed to create ip pool {name} with error: {code}, {data}"
    )

    yield {
        "name": name,
        "subnet": ip_pool_subnet
    }

    api_client.ippools.delete(name)


@pytest.fixture(scope='function', params=["dhcp", "pool"])
def lb_service(request, api_client, unique_name, nginx_deployment, ip_pool):
    namespace = "default"
    name = f"lb-{unique_name}-{request.param}"
    data = {
        "type": "service",
        "metadata": {
            "namespace": namespace,
            "name": name,
            "annotations": {
                "cloudprovider.harvesterhci.io/ipam": request.param
            }
        },
        "spec": {
            "type": "LoadBalancer",
            "sessionAffinity": None,
            "ports": [
                {
                    "name": "http",
                    "port": 8080,
                    "protocol": "TCP",
                    "targetPort": 80
                }
            ],
            "selector": {
                "name": nginx_deployment["name"]
            }
        }
    }

    yield {
        "namespace": namespace,
        "name": name,
        "data": data
    }

    code, data = api_client.loadbalancers.get()
    assert 200 == code, (code, data)
    lbs = data["data"]
    for lb in lbs:
        if name in lb["id"]:
            api_client.loadbalancers.delete(lb["id"])
            break
