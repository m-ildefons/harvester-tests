import base64
import yaml
from .base import BaseManager, DEFAULT_NAMESPACE, FLEET_DEFAULT_NAMESPACE


class HarvesterConfigManager(BaseManager):
    PATH_fmt = "v1/rke-machine-config.cattle.io.harvesterconfigs/{namespace}"

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
                    ssh_user, user_data, network_data, vm_namespace=DEFAULT_NAMESPACE):
        user_data = self._inject_guest_agent(user_data)

        return {
            "cpuCount": cpus,
            "diskSize": disks,
            "imageName": image_id,
            "memorySize": mems,
            "metadata": {
                "name": name,
                "namespace": FLEET_DEFAULT_NAMESPACE,
            },
            "networkName": network_id,
            "sshUser": ssh_user,
            "userData": base64.b64encode(user_data.encode('UTF-8')).decode('UTF-8'),
            "networkData": base64.b64encode(network_data.encode('UTF-8')).decode('UTF-8'),
            "vmNamespace": vm_namespace,
            "type": "rke-machine-config.cattle.io.harvesterconfig"
        }

    def create(self, name, cpus, mems, disks, image_id, network_id,
               ssh_user, vm_namespace=DEFAULT_NAMESPACE, user_data="",
               network_data="", *, raw=False):
        data = self.create_data(
            name=name,
            cpus=cpus,
            mems=mems,
            disks=disks,
            image_id=image_id,
            network_id=network_id,
            ssh_user=ssh_user,
            vm_namespace=vm_namespace,
            user_data=user_data,
            network_data=network_data
        )
        return self._create(
            self.PATH_fmt.format(namespace=FLEET_DEFAULT_NAMESPACE),
            json=data,
            raw=raw
        )

    def delete(self, name):
        return self._delete(
            (self.PATH_fmt+"/{id}").format(
                namespace=FLEET_DEFAULT_NAMESPACE,
                id=name
            )
        )
