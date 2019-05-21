import requests
from six.moves import urllib

from cloud_info_provider import exceptions
from cloud_info_provider import providers
from cloud_info_provider import utils


class MesosProvider(providers.BaseProvider):
    service_type = "compute"
    goc_service_type = None

    def __init__(self, opts):
        super(MesosProvider, self).__init__(opts)

        self.endpoint = None
        self.endpoint_type = None
        self.api_endpoints = []

        if not any([opts.mesos_endpoint,
                    opts.marathon_endpoint]):
            msg = ('You must provide a Mesos, Marathon or Chronos API '
                   'endpoint via --mesos-endpoint, --marathon-endpoint or '
                   '--chronos-endpoint respectively (alternatively using '
                   'the environment variables MESOS_ENDPOINT, '
                   'MARATHON_ENDPOINT or CHRONOS_ENDPOINT)')
            raise exceptions.MesosProviderException(msg)
        if len(filter(None,
                      [opts.mesos_endpoint,
                       opts.marathon_endpoint])) > 1:
            msg = ('Please provide only one API endpoint')
            raise exceptions.MesosProviderException(msg)
        if opts.mesos_endpoint:
            self.endpoint = opts.mesos_endpoint
            self.endpoint_type = 'mesos'
            self.api_endpoints = ['/metrics/snapshot', 'state']
        elif opts.marathon_endpoint:
            self.endpoint = opts.marathon_endpoint
            self.endpoint_type = 'marathon'
            self.api_endpoints = ['/v2/info', 'v2/leader']
        self.goc_service_type = 'eu.indigo-datacloud.%s' % self.endpoint_type

        self.static = providers.static.StaticProvider(opts)

    def get_site_info(self):
        d = {}
        for endp in self.api_endpoints:
            api_url = urllib.parse.urljoin(self.endpoint, endp)
            r = requests.get(api_url)
            d.update(r.json())
        return d

    def get_compute_shares(self, **kwargs):
        shares = self.static.get_compute_shares(prefix=True)
        return shares

    def get_compute_endpoints(self, **kwargs):
        ret = {
            'endpoints': {
                self.endpoint: {}},
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
        parser.add_argument(
            '--marathon-endpoint',
            metavar='<api-url>',
            default=utils.env('MARATHON_ENDPOINT'),
            help=('Specify Marathon API endpoint. '
                  'Defaults to env[MARATHON_ENDPOINT]'))
