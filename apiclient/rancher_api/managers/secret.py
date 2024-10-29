import base64
from .base import BaseManager, FLEET_DEFAULT_NAMESPACE


class SecretManager(BaseManager):
    PATH_fmt = "v1/secrets"

    def create_data(self, name, namespace, data, annotations=None):
        annotations = annotations or {}

        for key, value in data.items():
            data[key] = base64.b64encode(value.encode('UTF-8')).decode('UTF-8')

        return {
            "type": "secret",
            "metadata": {
                "namespace": namespace,
                "name": name,
                "annotations": annotations
            },
            "data": data
        }

    def create(self, name, data, namespace=FLEET_DEFAULT_NAMESPACE,
               annotations=None, *, raw=False):
        data = self.create_data(name, namespace, data, annotations=annotations)
        return self._create(self.PATH_fmt, json=data, raw=raw)
