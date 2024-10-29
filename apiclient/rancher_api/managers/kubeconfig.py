from .base import BaseManager, DEFAULT_NAMESPACE


class KubeConfigManager(BaseManager):
    PATH_fmt = "k8s/clusters/{cluster_id}/v1/harvester/kubeconfig"

    def create_data(self, name):
        return {
            "clusterRoleName": "harvesterhci.io:cloudprovider",
            "namespace": DEFAULT_NAMESPACE,
            "serviceAccountName": name
        }

    def create(self, name, cluster_id, *, raw=False):
        data = self.create_data(name)
        return self._create(self.PATH_fmt.format(cluster_id=cluster_id), json=data, raw=raw)
