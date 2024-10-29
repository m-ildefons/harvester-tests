import yaml
from .base import BaseManager, DEFAULT_NAMESPACE


class NodeTemplateManager(BaseManager):
    PATH_fmt = "v3/nodeTemplates/{uid}"

    def _inject_guest_agent(self, user_data):
        cmd = 'systemctl enable --now qemu-guest-agent.service'
        userdata = yaml.safe_load(user_data) or dict()
        pkgs = userdata.get('packages', [])
        runcmds = [' '.join(c) for c in userdata.get('runcmd', [])]
        if 'qemu-guest-agent' not in pkgs:
            userdata.setdefault('packages', []).append('qemu-guest-agent')

        if cmd not in runcmds:
            userdata.setdefault('runcmd', []).append(cmd.split())
        return f"#cloud-config\n{yaml.dump(userdata)}"

    def create_data(self, name, cpus, mems, disks, image_id, network_id,
                    ssh_user, cloud_credential_id, user_data, network_data,
                    engine_url, vm_namespace=DEFAULT_NAMESPACE):
        user_data = self._inject_guest_agent(user_data)

        return {
            "useInternalIpAddress": True,
            "type": "nodeTemplate",
            "engineInstallURL": engine_url,
            "engineRegistryMirror": [],
            "harvesterConfig": {
                "cloudConfig": "",
                "clusterId": "",
                "clusterType": "",
                "cpuCount": cpus,
                "diskBus": "virtio",
                "diskSize": disks,
                "imageName": image_id,
                "keyPairName": "",
                "kubeconfigContent": "",
                "memorySize": mems,
                "networkData": network_data,
                "networkModel": "virtio",
                "networkName": network_id,
                "networkType": "dhcp",
                "sshPassword": "",
                "sshPort": "22",
                "sshPrivateKeyPath": "",
                "sshUser": ssh_user,
                "userData": user_data,
                "vmAffinity": "",
                "vmNamespace": vm_namespace,
                "type": "harvesterConfig"
            },
            "namespaceId": "fixme",  # fixme is a real parameter
            "cloudCredentialId": cloud_credential_id,
            "labels": {},
            "name": name
        }

    def get(self, name="", *, raw=False):
        return self._get(self.PATH_fmt.format(uid=name), raw=raw)

    def create(self, name, cpus, mems, disks, image_id, network_id,
               ssh_user, cloud_credential_id, vm_namespace=DEFAULT_NAMESPACE,
               user_data="", network_data="", *, engine_url=None, raw=False):
        # TODO: need to align recommended in settings/engine-install-url
        engine_url = engine_url or 'https://get.docker.com'  # latest

        data = self.create_data(
            name=name,
            cpus=cpus,
            mems=mems,
            disks=disks,
            image_id=image_id,
            network_id=network_id,
            ssh_user=ssh_user,
            cloud_credential_id=cloud_credential_id,
            vm_namespace=vm_namespace,
            user_data=user_data,
            network_data=network_data,
            engine_url=engine_url
        )
        return self._create(self.PATH_fmt.format(uid="", ns=""), json=data, raw=raw)

    def delete(self, name, *, raw=False):
        return self._delete(self.PATH_fmt.format(uid=name), raw=raw)
