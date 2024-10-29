from .base import BaseManager


class NodePoolManager(BaseManager):
    PATH_fmt = "v3/nodepool/{ns}{uid}"

    def create_data(self, cluster_id, node_template_id, hostname_prefix, quantity):

        return {
            "controlPlane": True,
            "deleteNotReadyAfterSecs": 0,
            "drainBeforeDelete": False,
            "etcd": True,
            "quantity": quantity,
            "worker": True,
            "type": "nodePool",
            "clusterId": cluster_id,
            "nodeTemplateId": node_template_id,
            "hostnamePrefix": hostname_prefix
        }

    def get(self, name="", ns="", *, raw=False):
        if name == "":
            return self._get(self.PATH_fmt.format(uid="", ns=""), raw=raw)
        return self._get(self.PATH_fmt.format(uid=f":{name}", ns=ns), raw=raw)

    def create(self, cluster_id, node_template_id, hostname_prefix, quantity=1, *, raw=False):
        data = self.create_data(cluster_id, node_template_id, hostname_prefix, quantity)
        return self._create(self.PATH_fmt.format(uid="", ns=""), json=data, raw=raw)

    def delete(self, name, ns, *, raw=False):
        return self._delete(self.PATH_fmt.format(uid=f":{name}", ns=ns), raw=raw)
