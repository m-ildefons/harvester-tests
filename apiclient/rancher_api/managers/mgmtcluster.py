from .base import BaseManager, FLEET_DEFAULT_NAMESPACE


class MgmtClusterManager(BaseManager):
    PATH_fmt = "v1/provisioning.cattle.io.clusters{ns}{uid}"

    def create_data(self, cluster_name, cloud_provider_config_id, hostname_prefix,
                    harvester_config_name, k8s_version, cloud_credential_id, quantity):

        return {
            "type": "provisioning.cattle.io.cluster",
            "metadata": {
                "namespace": FLEET_DEFAULT_NAMESPACE,
                "name": cluster_name
            },
            "spec": {
                "rkeConfig": {
                    "chartValues": {
                        "rke2-calico": {},
                        "harvester-cloud-provider": {
                            "clusterName": cluster_name,
                            "cloudConfigPath": "/var/lib/rancher/rke2/etc/config-files/cloud-provider-config"  # noqa
                        }
                    },
                    "upgradeStrategy": {
                        "controlPlaneConcurrency": "1",
                        "controlPlaneDrainOptions": {
                            "deleteEmptyDirData": True,
                            "disableEviction": False,
                            "enabled": False,
                            "force": False,
                            "gracePeriod": -1,
                            "ignoreDaemonSets": True,
                            "ignoreErrors": False,
                            "skipWaitForDeleteTimeoutSeconds": 0,
                            "timeout": 120
                        },
                        "workerConcurrency": "1",
                        "workerDrainOptions": {
                            "deleteEmptyDirData": True,
                            "disableEviction": False,
                            "enabled": False,
                            "force": False,
                            "gracePeriod": -1,
                            "ignoreDaemonSets": True,
                            "ignoreErrors": False,
                            "skipWaitForDeleteTimeoutSeconds": 0,
                            "timeout": 120
                        }
                    },
                    "machineGlobalConfig": {
                        "cni": "calico",
                        "disable-kube-proxy": False,
                        "etcd-expose-metrics": False,
                        "profile": None
                    },
                    "machineSelectorConfig": [
                        {
                            "config": {
                                "cloud-provider-config": f"secret://{cloud_provider_config_id}",
                                "cloud-provider-name": "harvester",
                                "protect-kernel-defaults": False
                            }
                        }
                    ],
                    "etcd": {
                        "disableSnapshots": False,
                        "s3": None,
                        "snapshotRetention": 5,
                        "snapshotScheduleCron": "0 */5 * * *"
                    },
                    "registries": {
                        "configs": {},
                        "mirrors": {}
                    },
                    "machinePools": [
                        {
                            "name": "pool1",
                            "etcdRole": True,
                            "controlPlaneRole": True,
                            "workerRole": True,
                            "hostnamePrefix": hostname_prefix,
                            "labels": {},
                            "quantity": quantity,
                            "unhealthyNodeTimeout": "0m",
                            "machineConfigRef": {
                                "kind": "HarvesterConfig",
                                "name": harvester_config_name
                            }
                        }
                    ]
                },
                "machineSelectorConfig": [
                    {
                        "config": {}
                    }
                ],
                "kubernetesVersion": k8s_version,
                "defaultPodSecurityPolicyTemplateName": "",
                "cloudCredentialSecretName": cloud_credential_id,
                "localClusterAuthEndpoint": {
                    "enabled": False,
                    "caCerts": "",
                    "fqdn": ""
                }
            }
        }

    def get(self, name="", *, raw=False):
        if name == "":
            return self._get(self.PATH_fmt.format(uid="", ns=""), raw=raw)
        return self._get(
            self.PATH_fmt.format(uid=f"/{name}", ns=f"/{FLEET_DEFAULT_NAMESPACE}"),
            raw=raw
        )

    def create(self, name, cloud_provider_config_id, hostname_prefix,
               harvester_config_name, k8s_version, cloud_credential_id,
               quantity=1, *, raw=False):
        data = self.create_data(name, cloud_provider_config_id, hostname_prefix,
                                harvester_config_name, k8s_version, cloud_credential_id, quantity)
        return self._create(self.PATH_fmt.format(uid="", ns=""), json=data, raw=raw)

    def create_harvester(self, name, *, raw=False):
        return self._create(
            self.PATH_fmt.format(uid="", ns=""),
            json={
                "type": "provisioning.cattle.io.cluster",
                "metadata": {
                    "namespace": FLEET_DEFAULT_NAMESPACE,
                    "labels": {
                        "provider.cattle.io": "harvester"
                    },
                    "name": name,
                },
                "spec": {}
            },
            raw=raw
        )

    def delete(self, name, namespace=FLEET_DEFAULT_NAMESPACE, *, raw=False):
        return self._delete(self.PATH_fmt.format(uid=f"/{name}", ns=f"/{namespace}"))
