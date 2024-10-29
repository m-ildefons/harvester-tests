from .base import BaseManager, merge_dict


class ProjectManager(BaseManager):
    PATH_fmt = "v3/projects/{pid}"

    def get(self, project_id="", *, raw=False, **kwargs):
        if project_id:
            path = self.PATH_fmt.format(pid=project_id)
            params = dict() or kwargs.pop('params', {})
        else:
            path = self.PATH_fmt.format(pid="")
            params = merge_dict(dict(clusterId=self.api.cluster_id), kwargs.pop('params', {}))
        return self._get(path, from_cluster=False, raw=raw, params=params)

    def get_by_name(self, name, *, raw=False):
        resp = self.get(params=dict(name=name))
        if raw:
            return resp
        try:
            code, data = resp
            return code, data['data'][0]
        except KeyError:
            return code, data
        except IndexError:
            return 404, dict(type="error", status=404, code="notFound",
                             message=f"Failed to find project {name!r}")

    def delete(self, project_id, *, raw=False):
        path = self.PATH_fmt.format(pid=project_id)
        return self._delete(path, from_cluster=False, raw=raw)
