import requests
from six.moves import urllib

from cloud_info_provider import exceptions
from cloud_info_provider import providers
from cloud_info_provider import utils


class MesosProvider(providers.BaseProvider):
    def __init__(self, opts):
        super(MesosProvider, self).__init__(opts)

        self.opts = opts
        self.mesos_endpoint = opts.mesos_endpoint

        if not self.mesos_endpoint:
            msg = ('You must provide a Mesos API endpoint '
                   'via either --mesos-endpoint or '
                   'env[MESOS_ENDPOINT]')
            raise exceptions.MesosProviderException(msg)

        self.static = providers.static.StaticProvider(opts)

    def get_site_info(self):
        r = requests.get(urllib.parse.urljoin(self.mesos_endpoint,
                                              '/metrics/snapshot'))
        return r.json()

    def get_compute_shares(self, **kwargs):
        shares = self.static.get_compute_shares(prefix=True)
        return shares

    def get_compute_endpoints(self, **kwargs):
        ret = {
            'endpoints': {
                self.opts.mesos_endpoint: {}},
        }

        defaults = self.static.get_compute_endpoint_defaults(prefix=True)
        ret.update(defaults)
        return ret

    @staticmethod
    def populate_parser(parser):
        parser.add_argument(
            '--mesos-endpoint',
            metavar='<api-url>',
            default=utils.env('MESOS_ENDPOINT'),
            help=('Specify Mesos API endpoint. '
                  'Defaults to env[MESOS_ENDPOINT]'))
