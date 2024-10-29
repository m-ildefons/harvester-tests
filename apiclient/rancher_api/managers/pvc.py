from .base import BaseManager, DEFAULT_NAMESPACE


class PVCManager(BaseManager):
    PATH_fmt = "k8s/clusters/{cluster_id}/v1/persistentvolumeclaims"

    def get(self, cluster_id, name="", namespace=DEFAULT_NAMESPACE, raw=False):
        url = self.PATH_fmt.format(cluster_id=cluster_id)
        if namespace:
            url = f"{url}/{namespace}"
            if name:
                url = f"{url}/{name}"
        return self._get(url, raw=raw)

    def create(self, cluster_id, name, namespace=DEFAULT_NAMESPACE, raw=False):
        url = self.PATH_fmt.format(cluster_id=cluster_id)
        data = {
            "type": "persistentvolumeclaim",
            "metadata": {
                "namespace": namespace,
                "name": name
            },
            "spec": {
                "accessModes": [
                    "ReadWriteOnce"
                ],
                "volumeName": "",
                "resources": {
                    "requests": {
                        "storage": "1Gi"
                    }
                }
            }
        }
        return self._create(url, json=data, raw=raw)

    def delete(self, cluster_id, name, namespace=DEFAULT_NAMESPACE, raw=False):
        url = f"{self.PATH_fmt.format(cluster_id=cluster_id)}/{namespace}/{name}"
        return self._delete(url, raw=raw)
