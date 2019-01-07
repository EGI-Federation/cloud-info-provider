from cloud_info_provider.fetchers import base


class CloudFetcher(base.BaseFetcher):
    def __init__(self, opts, providers):
        super(CloudFetcher, self).__init__(opts, providers)
        self.templates = ('headers', 'clouddomain')

    def fetch(self):
        return self._get_info_from_providers('get_site_info')
