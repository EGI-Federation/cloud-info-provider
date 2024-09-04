from cloud_info_provider.collectors import base


class StorageCollector(base.BaseCollector):

    def __init__(self, *args):
        super(StorageCollector, self).__init__(*args)
        self.templates = ["storage"]

    def fetch(self):
        endpoints = self._get_info_from_providers("get_storage_endpoints")

        if not endpoints.get("endpoints"):
            return {}

        site_info = self._get_info_from_providers("get_site_info")
        static_storage_info = dict(endpoints, **site_info)
        static_storage_info.pop("endpoints")

        for endpoint in endpoints["endpoints"].values():
            endpoint.update(static_storage_info)

        info = {}
        info.update({"endpoints": endpoints})
        info.update({"static_storage_info": static_storage_info})

        return info
