from rancher_api.models import ChartSpec
from .base import BaseManager


class ChartManager(BaseManager):
    PATH_fmt = "k8s/clusters/{cluster_id}/v1/catalog.cattle.io.apps"
    CREATE_fmt = "k8s/clusters/{cluster_id}/v1/catalog.cattle.io.clusterrepos/rancher-charts"

    def get(self, cluster_id, namespace, name, raw=False):
        url = self.PATH_fmt.format(cluster_id=cluster_id)
        if namespace:
            url = f"{url}/{namespace}"
            if name:
                url = f"{url}/{name}"
        return self._get(url, raw=raw)

    def create(self, cluster_id, namespace, name, raw=False):
        url = self.CREATE_fmt.format(cluster_id=cluster_id) + "?action=install"
        data = ChartSpec(cluster_id, namespace, name).to_dict()
        return self._create(url, json=data, raw=raw)
