from .base import BaseManager

class ClusterRepoManager(BaseManager):
    PATH_fmt = "k8s/clusters/{cluster_id}/v1/catalog.cattle.io.clusterrepos/{name}"

    def get(self, cluster_id, name, raw=False):
        url = self.PATH_fmt.format(cluster_id=cluster_id, name=name)
        return self._get(url, raw=raw)
