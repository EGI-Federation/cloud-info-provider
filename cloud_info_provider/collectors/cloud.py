from cloud_info_provider.collectors import base


class CloudCollector(base.BaseCollector):

    def __init__(self, *args):
        super(CloudCollector, self).__init__(*args)
        self.templates = ("headers", "clouddomain")

    def fetch(self):
        return self._get_info_from_providers("get_site_info")
