import requests

from cloud_info_provider import exceptions
from cloud_info_provider import providers
from cloud_info_provider import utils


class OnedataProvider(providers.BaseProvider):
    service_type = "storage"
    goc_service_type = None

    def __init__(self, opts):
        super(OnedataProvider, self).__init__(opts)

        if not opts.onezone_api_url:
            msg = ('You must provide a OneData API '
                   'endpoint via --onedata-endpoint (alternatively using '
                   'the environment variable ONEZONE_API_URL)')
            raise exceptions.OnedataProviderException(msg)

        self.onezone_api_url = opts.onezone_api_url
        self.goc_service_type = 'eu.egi.cloud.storage-management.oneprovider'

        self.static = providers.static.StaticProvider(opts)

        self.headers = {}
        if opts.oidc_token:
            self.headers['X-Auth-Token'] = '%s: %s' % (opts.oidc_idp_prefix,
                                                       opts.oidc_token)

    def get_oneproviders_from_onezone(self):
        def _do_request(url):
            r = requests.get(url, headers=self.headers)
            if r.status_code == requests.codes.ok:
                return r.json()
            else:
                msg = 'Request failed: %s' % r.content
                raise exceptions.OnedataProviderException(msg)
        _url = '/'.join([self.onezone_api_url, 'onezone/providers'])
        try:
            oneprov_ids = _do_request(_url)['providers']
        except KeyError:
            oneprov_ids = []
        d = {}
        for oneprov_id in oneprov_ids:
            _oneprov_url = '/'.join([_url, oneprov_id])
            try:
                _domain = _do_request(_oneprov_url)['domain']
                d[_domain] = {'id': oneprov_id}
            except KeyError:
                raise exceptions.OnedataProviderException((
                    "Cannot get Oneprovider domains from Onezone"))
        return d

    def get_storage_endpoints(self, **kwargs):
        d_onezone = self.get_oneproviders_from_onezone()
        ret = {
            'endpoints': {},
        }

        defaults = self.static.get_storage_endpoint_defaults(prefix=True)
        defaults_endpoint = self.static.get_storage_endpoints()
        try:
            endp_data = defaults_endpoint.pop('endpoints')
        except KeyError:
            raise exceptions.OnedataProviderException((
                "Static configuration file does not contain"
                "Oneprovider endpoints"))
        defaults_endpoint.update(defaults)

        d_endpoints = {}
        for oneprov_domain, oneprov_data in endp_data.items():
            d_endpoints[oneprov_domain] = {}
            try:
                oneprov_id = d_onezone[oneprov_domain]
            except KeyError:
                print("No match found in Onezone providers list")
                continue
            d_endpoints[oneprov_domain]['onedata_id'] = oneprov_id
            aux = oneprov_data.copy()
            aux.update(defaults_endpoint)
            d_endpoints[oneprov_domain] = aux
        return {'endpoints': d_endpoints}

    @staticmethod
    def populate_parser(parser):
        parser.add_argument(
            '--onezone-api-url',
            metavar='<api-url>',
            default=utils.env('ONEZONE_API_URL'),
            help=('Specify OneData API endpoint with format: '
                  'https://onezone.example.org/api/v3. '
                  'Defaults to env[ONEZONE_API_URL]'))
        parser.add_argument(
            '--oidc-x-auth-token',
            metavar='<x-auth-token>',
            default=utils.env('IAM_ACCESS_TOKEN'),
            dest='oidc_token',
            help=('Specify OIDC X-Auth token to use when '
                  'authenticating with the API. Defaults '
                  'to env[IAM_ACCESS_TOKEN]'))
        parser.add_argument(
            '--oidc-idp-prefix',
            metavar='<idp-prefix>',
            dest='oidc_idp_prefix',
            help=('Specify OIDC X-Auth IdP prefix for the '
                  'X-Auth token'))
