from .base import BaseManager, DEFAULT_NAMESPACE


class ClusterDeploymentManager(BaseManager):
    PATH_fmt = "k8s/clusters/{cluster_id}/v1/apps.deployments"

    def get(self, cluster_id, namespace=DEFAULT_NAMESPACE, name="", raw=False):
        url = self.PATH_fmt.format(cluster_id=cluster_id)
        if namespace:
            url = f"{url}/{namespace}"
            if name:
                url = f"{url}/{name}"
        return self._get(url, raw=raw)

    def _create_data(self, namespace, name, image, pvc):
        workloadselector = f"apps.deployment-{namespace}-{name}"
        volumes, volume_mounts = [], []
        if pvc:
            volumes = [{
                "name": f"vol-{pvc}",
                "persistentVolumeClaim": {
                    "claimName": pvc
                }
            }]
            volume_mounts = [{
                "mountPath": "/data",
                "name": f"vol-{pvc}"
            }]

        return {
            "type": "apps.deployment",
            "metadata": {
                "namespace": namespace,
                "labels": {
                    "workload.user.cattle.io/workloadselector": workloadselector
                },
                "name": name
            },
            "spec": {
                "replicas": 1,
                "template": {
                    "spec": {
                        "restartPolicy": "Always",
                        "containers": [
                            {
                                "imagePullPolicy": "Always",
                                "name": "container-0",
                                "securityContext": {
                                    "runAsNonRoot": False,
                                    "readOnlyRootFilesystem": False,
                                    "privileged": False,
                                    "allowPrivilegeEscalation": False
                                },
                                "_init": False,
                                "volumeMounts": volume_mounts,
                                "__active": True,
                                "image": image
                            }
                        ],
                        "initContainers": [],
                        "imagePullSecrets": [],
                        "volumes": volumes,
                        "affinity": {}
                    },
                    "metadata": {
                        "labels": {
                            "name": name,
                            "workload.user.cattle.io/workloadselector": workloadselector
                        },
                        "namespace": namespace
                    }
                },
                "selector": {
                    "matchLabels": {
                        "workload.user.cattle.io/workloadselector": workloadselector
                    }
                }
            }
        }

    def create(self, cluster_id, namespace, name, image, pvc="", raw=False):
        url = self.PATH_fmt.format(cluster_id=cluster_id)
        data = self._create_data(namespace, name, image, pvc)
        return self._create(url, json=data, raw=raw)

    def delete(self, cluster_id, namespace, name, raw=False):
        url = f"{self.PATH_fmt.format(cluster_id=cluster_id)}/{namespace}/{name}"
        return self._delete(url, raw=raw)
