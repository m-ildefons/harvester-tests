from .base import BaseManager


class ClusterRegistrationTokenManager(BaseManager):
    PATH_fmt = "v3/clusterRegistrationTokens/{uid}:default-token"

    def get(self, name="", *, raw=False):
        return self._get(self.PATH_fmt.format(uid=name), raw=raw)
