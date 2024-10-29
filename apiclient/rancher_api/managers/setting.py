from .base import BaseManager


class SettingManager(BaseManager):
    PATH_fmt = "apis/management.cattle.io/v3/settings/{name}"

    def get(self, name="", *, raw=False):
        return self._get(self.PATH_fmt.format(name=name))
