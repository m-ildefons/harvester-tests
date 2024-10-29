from .base import BaseManager


class ProjectMemberManager(BaseManager):
    PATH_fmt = "v3/projectroletemplatebindings/{uid}"

    def get(self, uid="", *, raw=False, **kwargs):
        resp = self._get(self.PATH_fmt.format(uid=uid), from_cluster=False, **kwargs)
        if raw:
            return resp
        try:
            code, data = resp
            cluster_id = self.api.cluster_id
            data['data'] = [d for d in data['data'] if d['projectId'].startswith(cluster_id)]
            return code, data
        except KeyError:
            return code, data

    def get_by_project_id(self, project_id, *, raw=False):
        return self.get(params=dict(projectId=project_id), raw=raw)

    def create(self, project_id, user_pid, role_tid, *, raw=False):
        data = {
            "type": "projectroletemplatebinding",
            "projectId": project_id,
            "roleTemplateId": role_tid,
            "userPrincipalId": user_pid
        }
        return self._create(self.PATH_fmt.format(uid=""), json=data, raw=raw, from_cluster=False)

    def delete(self, uid, *, raw=False):
        return self._delete(self.PATH_fmt.format(uid=uid), raw=raw, from_cluster=False)
