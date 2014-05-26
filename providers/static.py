import argparse
import socket
import sys

import providers

static_info = {}

static_info['os_tpl'] = (
    {
        'image_name': 'SL64-x86_64',
        'image_version': '1.0',
        'marketplace_id': ('http://appdb.egi.eu/store/vm/image/'
                           '2c24de6c-e385-49f1-b64f-f9ff35e70f43:9/xml'),
        'occi_id': 'os#ef13c0be-4de6-428f-ad5b-8f32b31a54a1',
        'os_family': 'linux',
        'os_name': 'SL',
        'os_version': '6.4',
        'platform': 'amd64'
    },
    {
        'image_name': 'ubuntu-precise-server-amd64',
        'image_version': '1.0',
        'marketplace_id': ('http://appdb.egi.eu/store/vm/image/'
                           '703157c0-e509-44c8-8371-58beb44d80d6:8/xml'),
        'occi_id': 'os#c0a2f9e0-081a-419c-b9a5-8cb03b1decb5',
        'os_family': 'linux',
        'os_name': 'Ubuntu',
        'os_version': '12.04',
        'platform': 'amd64'
    },
    {
        'image_name': 'CernVM3',
        'image_version': '3.1.1.7',
        'marketplace_id': ('http://appdb.egi.eu/store/vm/image/'
                           'dfb2f33e-ba3f-4c5a-a387-6257e8558ba1:24/xml'),
        'occi_id': 'os#5364f77a-e1cb-4a6c-862e-96dc79c4ef67',
        'os_family': 'linux',
        'os_name': 'SL',
        'os_version': '6.4',
        'platform': 'amd64'
    },
)

static_info['resource_tpl'] = (
    {
        'occi_id': 'resource#tiny-with-disk',
        'memory': '512',
        'cpu': '1',
        'platform': 'amd64',
        'network': 'public'
    },
    {
        'occi_id': 'resource#small',
        'memory': '1024',
        'cpu': '1',
        'platform': 'amd64',
        'network': 'public'
    },
    {
        'occi_id': 'resource#medium',
        'memory': '4096',
        'cpu': '2',
        'platform': 'amd64',
        'network': 'public'
    },
    {
        'occi_id': 'resource#large',
        'memory': '8196',
        'cpu': '4',
        'platform': 'amd64',
        'network': 'public'},
    {
        'occi_id': 'resource#extra_large',
        'memory': '16384',
        'cpu': '8',
        'platform': 'amd64',
        'network': 'public'
    },
)


class StaticProvider(providers.BaseProvider):
    def __init__(self, *args):
        super(StaticProvider, self).__init__(*args)
        self._load_site_info()

        self._load_iaas_endpoint_info()

        self._load_staas_endpoint_info()

    def _load_site_info(self):
        self.site_info = {
            "site_name": self.opts.site_name,
            "site_production_level": self.opts.site_production_level,
        }

        if self.opts.full_bdii_ldif:
            needed_opts = ('site_url', 'site_ngi', 'site_country',
                           'site_latitude', 'site_longitude',
                           'site_general_contact', 'site_sysadmin_contact',
                           'site_security_contact',
                           'site_user_support_contact',
                           'site_bdii_host', 'site_bdii_port')

            self._parse_needed_opts(self.site_info,
                                    needed_opts,
                                    "full-bdii-ldif")

    def _load_staas_endpoint_info(self):
        aux = {}
        if self.opts.staas_endpoint:
            needed_opts = ('staas_capability', 'staas_middleware',
                           'staas_api_type', 'staas_api_version',
                           'staas_api_endpoint_technology',
                           'staas_api_authn_method',
                           'staas_middleware_version',
                           'staas_middleware_developer',
                           'staas_total_storage')
            self._parse_needed_opts(aux, needed_opts, "staas-endpoint")
            aux["staas_capabilities"] = tuple(aux.pop("staas_capability"))
            aux["endpoints"] = []
            for e in self.opts.iaas_endpoint:
                endpoint = {}
                endpoint["endpoint_url"] = e
                aux["endpoints"].append(endpoint)

        self.staas_endpoints = aux

    def _load_iaas_endpoint_info(self):
        aux = {}
        if self.opts.iaas_endpoint:
            needed_opts = ('iaas_capability', 'iaas_hypervisor',
                           'iaas_hypervisor_version', 'iaas_total_cores',
                           'iaas_total_ram', 'iaas_api_type',
                           'iaas_api_version', 'iaas_api_endpoint_technology',
                           'iaas_api_authn_method', 'iaas_middleware',
                           'iaas_middleware_version',
                           'iaas_middleware_developer')
            self._parse_needed_opts(aux, needed_opts, "iaas-endpoint")

            aux["iaas_capabilities"] = tuple(aux.pop("iaas_capability"))
            aux["endpoints"] = []
            for e in self.opts.iaas_endpoint:
                endpoint = {}
                endpoint["endpoint_url"] = e
                aux["endpoints"].append(endpoint)

            # This are only used if we have an endpoint
            self._load_flavors()
            self._load_images()

        self.iaas_endpoints = aux

    def _load_flavors(self):
        self.flavors = static_info.get("resource_tpl", [])

    def _load_images(self):
        self.images = static_info.get("os_tpl", [])

    def _parse_needed_opts(self, store_in, needed_opts, flag):
        for opt in needed_opts:
            value = getattr(self.opts, opt)
            if value is None:
                # TODO(aloga): use an exception here
                opt = opt.replace("_", "-")
                print >> sys.stderr, ('ERROR: Missing option "--%s" is '
                                      'mandatory with "%s"' %
                                      (opt, flag))
                sys.exit(1)

            store_in[opt] = value

    def get_site_info(self):
        return self.site_info

    def get_images(self):
        return self.images

    def get_templates(self):
        return self.flavors

    def get_iaas_endpoints(self):
        return self.iaas_endpoints

    def get_staas_endpoints(self):
        return self.staas_endpoints

    @staticmethod
    def populate_parser(parser):
        """Populate the argparser 'parser' with the needed options."""

        # Site info
        parser.add_argument('--site-name',
            required=True,
            help='Site name.')

        parser.add_argument('--site-url',
            metavar='URL',
            help='Site URL.')

        parser.add_argument('--site-ngi',
            metavar='NGI',
            help='Site NGI.')

        parser.add_argument('--site-country',
            help='Site Country.')

        parser.add_argument('--site-latitude',
            metavar='LATITUDE',
            type=float,
            help='Site Latitude.')

        parser.add_argument('--site-longitude',
            metavar='LONGITUDE',
            type=float,
            help='Site Longitude.')

        parser.add_argument('--site-general-contact',
            metavar='EMAIL',
            help='Site general contact email.')

        parser.add_argument('--site-sysadmin-contact',
            metavar='EMAIL',
            help='Site sysadmin contact email.')

        parser.add_argument('--site-security-contact',
            metavar='EMAIL',
            help='Site security contact email.')

        parser.add_argument('--site-user-support-contact',
            metavar='EMAIL',
            help='Site user-support contact email.')

        parser.add_argument('--site-production-level',
            default='production',
            help='Site production level.')

        parser.add_argument('--site-bdii-host',
            metavar='HOSTNAME',
            default=socket.getfqdn(),
            help='Site BDII hostname.')

        parser.add_argument('--site-bdii-port',
            metavar='PORT',
            type=int,
            default=2170,
            help='Site BDII hostname.')

        # IaaS
        parser.add_argument('--iaas-endpoint',
            metavar='URL',
            default=[],
            action='append',
            help=('IaaS endpoints. Can be used severail times to specify'
                  'a list of endpoints'))

        parser.add_argument('--iaas-capability',
            metavar='CAPABILITY',
            action='append',
            default=['cloud.managementSystem', 'cloud.vm.uploadImage'],
            help=('IaaS capability. Can be used several times to specify '
                  'a list of capabilities'))

        parser.add_argument('--iaas-hypervisor',
            metavar='HYPERVISOR',
            help='Hypervisor used (i.e. "KVM", "Xen", etc.)')

        parser.add_argument('--iaas-hypervisor-version',
            metavar='VERSION',
            help='Hypervisor version.')

        parser.add_argument('--iaas-total-ram',
            metavar='RAM',
            type=float,
            help='Total RAM available in GB.')

        parser.add_argument('--iaas-total-cores',
            metavar='CORES',
            type=int,
            help='Total number of cores.')

        parser.add_argument('--iaas-middleware',
            help='Name of the middleware used.')

        parser.add_argument('--iaas-middleware-version',
            help='Middleware version.')

        parser.add_argument('--iaas-middleware-developer',
            help='Middleware developer.')

        parser.add_argument('--iaas-api-type',
            metavar='API_TYPE',
            default='OCCI',
            help="IaaS API Type")
        parser.add_argument('--iaas-api-version',
            metavar='API_VERSION',
            default='1.1',
            help="IaaS API version")
        parser.add_argument('--iaas-api-endpoint-technology',
            metavar='API_TECHNOLOGY',
            default='REST',
            help=argparse.SUPPRESS)
        parser.add_argument('--iaas-api-authn-method',
            default='X509-VOMS',
            help=argparse.SUPPRESS)

        # Staas
        parser.add_argument('--staas-endpoint',
            metavar='URL',
            default=[],
            action='append',
            help=('StaaS endpoints. Can be used severail times to specify'
                  'a list of endpoints'))

        parser.add_argument('--staas-capability',
            metavar='CAPABILITY',
            action='append',
            default=['cloud.data.upload'],
            help=('StaaS capability. Can be used several times to specify '
                  'a list of capabilities'))

        parser.add_argument('--staas-total-storage',
            metavar='STORAGE_SIZE',
            type=float,
            help='Total storage available in GB.')

        parser.add_argument('--staas-middleware',
            help='Name of the middleware used.')

        parser.add_argument('--staas-middleware-version',
            help='Middleware version.')

        parser.add_argument('--staas-middleware-developer',
            help='Middleware developer.')

        parser.add_argument('--staas-api-type',
            metavar='API_TYPE',
            default='CDMI',
            help="StaaS API Type")
        parser.add_argument('--staas-api-version',
            metavar='API_VERSION',
            default='1.0.1',
            help="StaaS API version")
        parser.add_argument('--staas-api-endpoint-technology',
            metavar='API_TECHNOLOGY',
            default='REST',
            help=argparse.SUPPRESS)
        parser.add_argument('--staas-api-authn-method',
            default='X509-VOMS',
            help=argparse.SUPPRESS)
