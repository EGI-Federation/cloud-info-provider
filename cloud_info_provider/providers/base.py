import logging

from cloud_info_provider.providers import gocdb, ssl_utils


class BaseProvider(object):
    def __init__(self, opts, **kwargs):
        self.opts = opts
        self.setup_logging()
        self._ca_info = {}
        self._goc_info = {}
        self._last_goc_url = ""

    def _get_endpoint_ca_information(self, url, **kwargs):
        if url not in self._ca_info:
            ca_info = ssl_utils.get_endpoint_ca_information(url, **kwargs)
            self._ca_info[url] = ca_info
        return self._ca_info[url]

    def get_goc_info(self, url=None, insecure=False):
        if not hasattr(self, "goc_service_type"):
            return {}
        if not url:
            url = self._last_goc_url
        if url not in self._goc_info:
            # pylint: disable=no-member
            self._goc_info[url] = gocdb.find_in_gocdb(url,
                                                      self.goc_service_type,
                                                      insecure)
        self._last_goc_url = url
        return self._goc_info[url]

    def get_site_info(self, **kwargs):
        return {}

    def get_images(self, **kwargs):
        return {}

    def get_templates(self, **kwargs):
        return {}

    def get_instances(self, **kwargs):
        return {}

    def get_compute_shares(self, **kwargs):
        return {}

    def get_compute_share(self, **kwargs):
        return {}

    def get_compute_quotas(self, **kwargs):
        return {}

    def get_compute_endpoints(self, **kwargs):
        return {}

    def get_storage_endpoints(self, **kwargs):
        return {}

    @staticmethod
    def populate_parser(parser):
        '''Populate the argparser 'parser' with the needed options.'''

    def setup_logging(self):
        level = logging.DEBUG if self.opts.debug else logging.INFO
        logging.basicConfig(level=level)
