import requests

from cloud_info_provider import exceptions
from cloud_info_provider import providers
from cloud_info_provider import utils


class MesosProvider(providers.BaseProvider):
    service_type = "compute"
    goc_service_type = None

    def __init__(self, opts):
        super(MesosProvider, self).__init__(opts)

        if not opts.mesos_endpoint:
            msg = ('You must provide a Mesos, Marathon or Chronos API '
                   'endpoint via --mesos-endpoint (alternatively using '
                   'the environment variable MESOS_ENDPOINT)')
            raise exceptions.MesosProviderException(msg)

        if not opts.mesos_framework:
            msg = ('You must provide the endpoint URL to connect to')
            raise exceptions.MesosProviderException(msg)

        self.framework_url = opts.mesos_endpoint
        self.api_endpoints = []
        self.insecure = opts.insecure
        self.cacert = opts.mesos_cacert
        if self.insecure:
            requests.packages.urllib3.disable_warnings()
            self.cacert = False

        if opts.mesos_framework == 'mesos':
            self.api_endpoints = ['/metrics/snapshot', 'state']
        elif opts.mesos_framework == 'marathon':
            self.api_endpoints = ['v2/info', 'v2/leader']
        self.goc_service_type = 'eu.indigo-datacloud.%s' % opts.mesos_framework

        self.static = providers.static.StaticProvider(opts)

        self.headers = {}
        if opts.oidc_token:
            self.headers['Authorization'] = 'Bearer %s' % opts.oidc_token

    def get_compute_shares(self, **kwargs):
        shares = self.static.get_compute_shares(prefix=True)
        return shares

    def get_compute_endpoints(self, **kwargs):
        ret = {
            'endpoints': {
                self.framework_url: {}},
        }

        # just gather the relevant variables
        global_f = ('total_cores', 'total_ram', 'total_accelerators',
                    'local_volumes_host_base_path',
                    'persistent_storage_drivers',
                    'load_balancer_ips')
        endp_f = global_f

        defaults = self.static.get_compute_endpoint_defaults(prefix=True)
        ret['compute_service_name'] = self.framework_url
        ret.update(defaults)

        defaults_endpoint = self.static.get_compute_endpoints(
            global_f=global_f, endp_f=endp_f)
        endp_data = defaults_endpoint.pop('endpoints')
        if self.framework_url in endp_data.keys():
            d = {k: v
                 for (k, v) in endp_data[self.framework_url].items()
                 if v is not None}
            ret.update(d)

        d = ret.copy()
        # add external endpoint URL
        d['framework_url'] = self.framework_url
        for api_endp in self.api_endpoints:
            api_url = '/'.join([self.framework_url, api_endp])
            r = requests.get(api_url, headers=self.headers, verify=self.cacert)
            if r.status_code == requests.codes.ok:
                d.update(r.json())
            else:
                msg = 'Request failed: %s' % r.content
                raise exceptions.MesosProviderException(msg)
        ret['endpoints'][self.framework_url] = d

        return ret

    @staticmethod
    def populate_parser(parser):
        parser.add_argument(
            '--mesos-framework',
            choices=['mesos', 'marathon', 'chronos'],
            help=('Select the type of framework to collect data from '
                  '(required).'))
        parser.add_argument(
            '--mesos-endpoint',
            metavar='<api-url>',
            default=utils.env('MESOS_ENDPOINT'),
            help=('Specify Mesos|Marathon API endpoint. '
                  'Defaults to env[MESOS_ENDPOINT]'))
        parser.add_argument(
            '--mesos-cacert',
            metavar='<ca-certificate>',
            default=utils.env('MESOS_ENDPOINT'),
            help=('Specify a CA bundle file to verify HTTPS connections '
                  'to Mesos endpoints.'))
        parser.add_argument(
            '--oidc-auth-bearer-token',
            metavar='<bearer-token>',
            default=utils.env('IAM_ACCESS_TOKEN'),
            dest='oidc_token',
            help=('Specify OIDC bearer token to use when '
                  'authenticating with the API. Defaults '
                  'to env[IAM_ACCESS_TOKEN]'))
