from urllib.parse import urlencode
from .base import BaseManager, FLEET_DEFAULT_NAMESPACE


class CloudCredentialManager(BaseManager):
    PATH_fmt = "v3/cloudcredentials{uid}"

    def create_data(self, name, kubeconfig, cluster_id=""):
        if cluster_id == "":
            harvester_credential_config = {
                "clusterType": "external",
                "kubeconfigContent": kubeconfig
            }
        else:
            harvester_credential_config = {
                "clusterType": "imported",
                "clusterId": cluster_id,
                "kubeconfigContent": kubeconfig
            }

        return {
            "type": "provisioning.cattle.io/cloud-credential",
            "metadata": {
                "generateName": "cc-",
                "namespace": FLEET_DEFAULT_NAMESPACE
            },
            "_name": name,
            "annotations": {
                "provisioning.cattle.io/driver": "harvester"
            },
            "harvestercredentialConfig": harvester_credential_config,
            "_type": "provisioning.cattle.io/cloud-credential",
            "name": name
        }

    def create(self, name, kubeconfig, cluster_id="", *, raw=False):
        data = self.create_data(name, kubeconfig, cluster_id)
        return self._create(self.PATH_fmt.format(uid="", ns=""), json=data, raw=raw)

    def get(self, name="", *, raw=False, **kwargs):
        uid = f"/{name}" if name else ""

        if not kwargs:
            return self._get(self.PATH_fmt.format(uid=uid), raw=raw)

        return self._get(self.PATH_fmt.format(uid=f"{uid}?{urlencode(kwargs)}"), raw=raw)

    def delete(self, name, *, raw=False):
        return self._delete(self.PATH_fmt.format(uid=f"/{name}"), raw=raw)
