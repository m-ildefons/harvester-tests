import json
from weakref import ref


DEFAULT_NAMESPACE = "default"
FLEET_DEFAULT_NAMESPACE = "fleet-default"


def merge_dict(src, dest):
    for k, v in src.items():
        if isinstance(dest.get(k), dict) and isinstance(v, dict):
            merge_dict(v, dest[k])
        else:
            dest[k] = v
    return dest


class BaseManager:
    def __init__(self, api):
        self._api = ref(api)

    @property
    def api(self):
        if self._api() is None:
            raise ReferenceError("API object no longer exists")
        return self._api()

    def _delegate(self, meth, path, *, raw=False, **kwargs):
        func = getattr(self.api, meth)
        resp = func(path, **kwargs)

        if raw:
            return resp
        try:
            if "json" in resp.headers.get('Content-Type', ""):
                rval = resp.json()
            else:
                rval = resp.text
            return resp.status_code, rval
        except json.decoder.JSONDecodeError as e:
            return resp.status_code, dict(error=e, response=resp)

    def _get(self, path, *, raw=False, **kwargs):
        return self._delegate("_get", path, raw=raw, **kwargs)

    def _create(self, path, *, raw=False, **kwargs):
        return self._delegate("_post", path, raw=raw, **kwargs)

    def _update(self, path, data, *, raw=False, as_json=True, **kwargs):
        if as_json:
            kwargs.update(json=data)
        else:
            kwargs.update(data=data)

        return self._delegate("_put", path, raw=raw, **kwargs)

    def _delete(self, path, *, raw=False, **kwargs):
        return self._delegate("_delete", path, raw=raw, **kwargs)
