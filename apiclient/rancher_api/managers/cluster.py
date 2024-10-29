from .base import BaseManager


class ClusterManager(BaseManager):
    PATH_fmt = "v3/cluster/{uid}"
    PATH1_fmt = "v3/clusters/{uid}"

    def create_data(self, name, k8s_version, kubeconfig):

        return {
            "dockerRootDir": "/var/lib/docker",
            "enableClusterAlerting": False,
            "enableClusterMonitoring": False,
            "enableNetworkPolicy": False,
            "windowsPreferedCluster": False,
            "type": "cluster",
            "name": name,
            "rancherKubernetesEngineConfig": {
                "addonJobTimeout": 45,
                "enableCriDockerd": False,
                "ignoreDockerVersion": True,
                "rotateEncryptionKey": False,
                "sshAgentAuth": False,
                "type": "rancherKubernetesEngineConfig",
                "kubernetesVersion": k8s_version,
                "authentication": {
                    "strategy": "x509",
                    "type": "authnConfig"
                },
                "dns": {
                    "type": "dnsConfig",
                    "nodelocal": {
                            "type": "nodelocal",
                            "ip_address": "",
                            "node_selector": None,
                            "update_strategy": {}
                    }
                },
                "network": {
                    "mtu": 0,
                    "plugin": "canal",
                    "type": "networkConfig",
                    "options": {
                        "flannel_backend_type": "vxlan"
                    }
                },
                "ingress": {
                    "defaultBackend": False,
                    "defaultIngressClass": True,
                    "httpPort": 0,
                    "httpsPort": 0,
                    "provider": "nginx",
                    "type": "ingressConfig"
                },
                "monitoring": {
                    "provider": "metrics-server",
                    "replicas": 1,
                    "type": "monitoringConfig"
                },
                "services": {
                    "type": "rkeConfigServices",
                    "kubeApi": {
                        "alwaysPullImages": False,
                        "podSecurityPolicy": False,
                        "serviceNodePortRange": "30000-32767",
                        "type": "kubeAPIService",
                        "secretsEncryptionConfig": {
                            "enabled": False,
                            "type": "secretsEncryptionConfig"
                        }
                    },
                    "etcd": {
                        "creation": "12h",
                        "extraArgs": {
                            "heartbeat-interval": 500,
                            "election-timeout": 5000
                        },
                        "gid": 0,
                        "retention": "72h",
                        "snapshot": False,
                        "uid": 0,
                        "type": "etcdService",
                        "backupConfig": {
                            "enabled": True,
                            "intervalHours": 12,
                            "retention": 6,
                            "safeTimestamp": False,
                            "timeout": 300,
                            "type": "backupConfig"
                        }
                    }
                },
                "upgradeStrategy": {
                    "maxUnavailableControlplane": "1",
                    "maxUnavailableWorker": "10%",
                    "drain": "false",
                    "nodeDrainInput": {
                        "deleteLocalData": False,
                        "force": False,
                        "gracePeriod": -1,
                        "ignoreDaemonSets": True,
                        "timeout": 120,
                        "type": "nodeDrainInput"
                    },
                    "maxUnavailableUnit": "percentage"
                },
                "cloudProvider": {
                    "type": "cloudProvider",
                    "name": "harvester",
                    "harvesterCloudProvider": {
                        "cloudConfig": kubeconfig
                    }
                }
            },
            "localClusterAuthEndpoint": {
                "enabled": True,
                "type": "localClusterAuthEndpoint"
            },
            "labels": {},
            "scheduledClusterScan": {
                "enabled": False,
                "scheduleConfig": None,
                "scanConfig": None
            }
        }

    def get(self, name="", *, raw=False):
        return self._get(self.PATH_fmt.format(uid=name), raw=raw)

    def create(self, name, k8s_version, kubeconfig, *, raw=False):
        data = self.create_data(name, k8s_version, kubeconfig)
        return self._create(self.PATH_fmt.format(uid=""), json=data, raw=raw)

    def delete(self, name, *, raw=False):
        return self._delete(self.PATH_fmt.format(uid=name), raw=raw)

    def generate_kubeconfig(self, name, *, raw=False):
        return self._create(
            self.PATH1_fmt.format(uid=name),
            raw=raw,
            params={'action': 'generateKubeconfig'}
        )

    def explore(self, name):
        from rancher_api.cluster_api import ClusterExploreAPI  # circular dependency
        return ClusterExploreAPI(self.api.endpoint, self.api.session, name)
