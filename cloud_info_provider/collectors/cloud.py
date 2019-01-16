from cloud_info_provider.collectors import base


class CloudCollector(base.BaseCollector):
    def __init__(self, opts, providers):
        super(CloudCollector, self).__init__(opts, providers)
        self.templates = ('headers', 'clouddomain')

    def fetch(self):
        return self._get_info_from_providers('get_site_info')
