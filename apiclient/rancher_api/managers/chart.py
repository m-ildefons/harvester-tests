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

    def data(self, cluster_id, namespace, name):
        return ChartSpec(cluster_id, namespace, name).to_dict()

    def create_with_data(self, cluster_id, data, raw=False):
        url = self.CREATE_fmt.format(cluster_id=cluster_id) + "?action=install"
        return self._create(url, json=data, raw=raw)

    def create(self, cluster_id, namespace, name, raw=False):
        data = self.data(cluster_id, namespace, name)
        return self.create_with_data(cluster_id=cluster_id, data=data, raw=raw)
