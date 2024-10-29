from .base import BaseManager


class StorageClassManager(BaseManager):
    PATH_fmt = "v1/storage.k8s.io.storageclasses/{uid}"
    DEFAULT_KEY = "storageclass.kubernetes.io/is-default-class"

    def get(self, name="", *, raw=False):
        return self._get(self.PATH_fmt.format(uid=name), raw=raw)

    def create(self, *args, **kwargs):
        raise NotImplementedError("Not implemented yet.")

    def update(self, *args, **kwargs):
        raise NotImplementedError("Not implemented yet.")

    def delete(self, name, *, raw=False):
        return self._delete(self.PATH_fmt.format(uid=name))
