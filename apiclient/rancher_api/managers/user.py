from collections.abc import Mapping
from rancher_api.models import UserSpec
from .base import BaseManager, merge_dict


class UserManager(BaseManager):
    PATH_fmt = "v3/users/{uid}"
    ROLE_fmt = "v3/globalrolebindings/{uid}"

    Spec = UserSpec

    def get(self, uid="", *, raw=False, **kwargs):
        path = self.PATH_fmt.format(uid=uid)
        return self._get(path, raw=raw, **kwargs)

    def get_by_name(self, name, *, raw=False):
        resp = self.get(raw=raw, params=dict(username=name))
        if raw:
            return resp
        try:
            code, data = resp
            return code, data['data'][0]
        except IndexError:
            return 404, dict(type="error", status=404, code="NotFound",
                             message=f"username {name!r} not found")

    def create(self, username, spec, *, raw=False):
        if isinstance(spec, self.Spec):
            spec = spec.to_dict(username)
        path = self.PATH_fmt.format(uid="")
        return self._create(path, json=spec, raw=raw)

    def update(self, uid, spec, *, raw=False, as_json=True, **kwargs):
        path = self.PATH_fmt.format(uid=uid)
        _, user = self.get(uid)
        if isinstance(spec, self.Spec):
            spec = spec.to_dict(user['username'])
        if isinstance(spec, Mapping) and as_json:
            spec = merge_dict(spec, user)
        return self._update(path, spec, raw=raw, as_json=as_json, **kwargs)

    def update_password(self, uid, passwd, *, raw=False):
        path = self.PATH_fmt.format(uid=uid)
        data = dict(newPassword=passwd)
        return self._create(path, raw=raw, json=data, params=dict(action="setpassword"))

    def delete(self, uid, *, raw=False):
        path = self.PATH_fmt.format(uid=uid)
        return self._delete(path, raw=raw)

    def get_roles(self, uid, *, raw=False, **kwargs):
        path = self.ROLE_fmt.format(uid="")
        params = merge_dict(dict(userId=uid), kwargs.pop('params', {}))
        return self._get(path, params=params, raw=raw, **kwargs)

    def add_role(self, uid, role_id, *, raw=False):
        path = self.ROLE_fmt.format(uid="")
        data = dict(type="globalRoleBinding", userId=uid, globalRoleId=role_id)
        return self._create(path, json=data, raw=raw)

    def delete_role(self, uid, role_id, *, raw=False):
        try:
            code, data = self.get_roles(uid, params=dict(globalRoleId=role_id))
            ruid = data['data'][0]['id']
            return self._delete(self.ROLE_fmt.format(uid=ruid), raw=raw)
        except IndexError:
            return 404, dict(type='error', status=404, code='NotFound',
                             message=f"User {uid!r} haven't Role {role_id!r}")
        except KeyError:
            return code, data
