#!/usr/bin/env python

import argparse
import os
import sys

interface = {
    'IaaS_api': 'OCCI',
    'IaaS_api_version': '1.1',
    'IaaS_api_endpoint_technology': 'REST',
    'IaaS_api_authorization_method': 'X509-VOMS',
    'STaaS_api': 'CDMI',
    'STaaS_api_version': '1.0.1',
    'STaaS_api_endpoint_technology': 'REST',
    'STaaS_api_authorization_method': 'X509-VOMS',
}

provider = {
    'site_name': 'PRISMA-INFN-BARI',
    'www': 'http://recas-pon.ba.infn.it/',
    'country': 'IT',
    'site_longitude': '16.88',
    'site_latitude': '41.11',
    'affiliated_ngi': 'NGI_IT',
    'user_support_contact': 'prisma-iaas-open-support@lists.ba.infn.it',
    'general_contact': 'prisma-iaas-open-support@lists.ba.infn.it',
    'sysadmin_contact': 'prisma-iaas-open-support@lists.ba.infn.it',
    'security_contact': 'prisma-iaas-open-support@lists.ba.infn.it',
    'production_level': 'production',
    'site_bdii_host': 'prisma-cloud.ba.infn.it',
    'site_bdii_port': '2170',


    'site_total_cpu_cores': '300',
    'site_total_ram_gb': '600',
    'site_total_storage_gb': '51200',

    'iaas_middleware': 'OpenStack Nova',
    'iaas_middleware_version': 'havana',
    'iaas_middleware_developer': 'OpenStack',
    'iaas_hypervisor': 'KVM',
    'iaas_hypervisor_version': '1.5.0',
    'iaas_capabilities': ('cloud.managementSystem', 'cloud.vm.uploadImage'),
}

provider['iaas_endpoints'] = (
    {
        'endpoint_url': 'https://prisma-cloud.ba.infn.it:8787',
        'endpoint_interface': interface['IaaS_api'],
        'service_type_name': provider['iaas_middleware'],
        'service_type_version': provider['iaas_middleware_version'],
        'service_type_developer': provider['iaas_middleware_developer'],
        'interface_version': interface['IaaS_api_version'],
        'endpoint_technology': interface['IaaS_api_endpoint_technology'],
        'auth_method': interface['IaaS_api_authorization_method']
    },
)


provider['os_tpl'] = (
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

provider['resource_tpl'] = (
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

provider['staas_middleware'] = 'OpenStack Swift'
provider['staas_middleware_version'] = 'havana'
provider['staas_middleware_developer'] = 'OpenStack'
provider['staas_capabilities'] = 'cloud.data.upload'

provider['staas_endpoints'] = (
    {
        'endpoint_url': 'https://prisma-swift.ba.infn.it:8080',
        'endpoint_interface': interface['STaaS_api'],
        'service_type_name': provider['staas_middleware'],
        'service_type_version': provider['staas_middleware_version'],
        'service_type_developer': provider['staas_middleware_developer'],
        'interface_version': interface['STaaS_api_version'],
        'endpoint_technology': interface['STaaS_api_endpoint_technology'],
        'auth_method': interface['STaaS_api_authorization_method']
    },
)


class BaseBDII(object):
    def __init__(self, templates, info):
        self.info = info
        self.ldif = {}
        self.templates = templates
        for tpl in self.templates:
            with open('templates/%s.ldif' % tpl, 'r') as f:
                self.ldif[tpl] = f.read()

    def _format_template(self, template, info=None, extra={}):
        if not info:
            info = self.info
        fd = info.copy()
        fd.update(extra)
        return self.ldif.get(template, "") % fd


class StaaSBDII(BaseBDII):
    def __init__(self, provider):
        templates = ("storage_service", "storage_endpoint", "storage_capacity")
        super(StaaSBDII, self).__init__(templates, provider)

    def render(self):
        output = []
        output.append(self._format_template("storage_service"))

        for endpoint in provider['staas_endpoints']:
            output.append(self._format_template("storage_endpoint",
                                                extra=endpoint))

        output.append(self._format_template("storage_capacity"))

        return "\n".join(output)


class IaaSBDII(BaseBDII):
    def __init__(self, provider):
        templates = ("compute_service", "compute_endpoint",
                     "execution_environment", "application_environment")
        super(IaaSBDII, self).__init__(templates, provider)

    def render(self):
        output = []
        output.append(self._format_template("compute_service"))

        for endpoint in provider['iaas_endpoints']:
            output.append(self._format_template("compute_endpoint",
                                                extra=endpoint))

        for ex_env in provider['resource_tpl']:
            output.append(self._format_template("execution_environment",
                                                extra=ex_env))

        for app_env in provider['os_tpl']:
            app_env.setdefault("image_description",
                               ("%(image_name)s version %(image_version)s on "
                                "%(os_family)s %(os_name)s %(os_version)s "
                                "%(platform)s" % app_env))
            output.append(self._format_template("application_environment",
                                                extra=app_env))

        return "\n".join(output)


class CloudBDII(BaseBDII):
    def __init__(self, provider):
        self.services = []
        if provider.get('iaas_endpoints', None):
            self.services.append(IaaSBDII(provider))

        if provider.get('staas_endpoints', None):
            self.services.append(StaaSBDII(provider))

        self.templates = ("headers", "domain", "bdii")
        super(CloudBDII, self).__init__(self.templates, provider)

    def render(self):
        output = []
        for tpl in self.templates:
            output.append(self._format_template(tpl))
        for i in self.services:
            output.append(i.render())
        return "\n".join(output)


class OpenStackProvider(object):
    def __init__(self, opts):
        try:
            import novaclient.client
        except ImportError:
            print >> sys.stderr, "ERROR: Cannot import nova module."
            sys.exit(1)

        (os_username, os_password, os_tenant_name, os_tenant_id,
            os_auth_url, cacert, insecure) = (
                opts.os_username, opts.os_password,
                opts.os_tenant_name, opts.os_tenant_id,
                opts.os_auth_url, opts.os_cacert, opts.insecure)

        if not os_username:
            print >> sys.stderr, ("ERROR, You must provide a username "
                                  "via either --os-username or "
                                  "env[OS_USERNAME]")
            sys.exit(1)

        if not os_password:
            print >> sys.stderr, ("ERROR, You must provide a password "
                                  "via either --os-password or "
                                  "env[OS_PASSWORD]")
            sys.exit(1)

        if not os_tenant_name and not os_tenant_id:
            print >> sys.stderr, ("You must provide a tenant name "
                                  "or tenant id via --os-tenant-name, "
                                  "--os-tenant-id, env[OS_TENANT_NAME] "
                                  "or env[OS_TENANT_ID]")
            sys.exit(1)

        if not os_auth_url:
            print >> sys.stderr, ("You must provide an auth url "
                                  "via either --os-auth-url or "
                                  "env[OS_AUTH_URL] ")
            sys.exit(1)

        client_cls = novaclient.client.get_client_class("2")
        self.api = client_cls(os_username,
                              os_password,
                              os_tenant_name,
                              tenant_id=os_tenant_id,
                              auth_url=os_auth_url,
                              insecure=insecure,
                              cacert=cacert)

        self.api.authenticate()

    def get_templates(self):
        flavors = []

        for flavor in self.api.flavors.list(detailed=True):
            if not flavor.is_public:
                continue
            aux = {
                'occi_id': 'resource#%s' % flavor.name,
                'memory': flavor.ram,
                'cpu': flavor.vcpus,
                'network': 'public',
                'platform': None,
            }
            flavors.append(aux)
        return flavors

    def get_images(self):
        images = []

        template = {
            'image_name': None,
            'image description': None,
            'image_version': None,
            'marketplace_id': None,
            'occi_id': None,
            'os_family': None,
            'os_name': None,
            'os_version': None,
            'platform': None,
        }

        for image in self.api.images.list(detailed=True):
            aux = template.copy()
            aux.update({'image_name': image.name,
                        'occi_id': 'os#%s' % image.id,
                        'image_description': image.name,
            })
            image.metadata.pop("image_name", None)
            image.metadata.pop("occi_id", None)
            aux.update(image.metadata)
            images.append(aux)
        return images

    @staticmethod
    def populate_parser(parser):
        parser.add_argument('--os-username',
            metavar='<auth-user-name>',
            default=env('OS_USERNAME', 'NOVA_USERNAME'),
            help='Defaults to env[OS_USERNAME].')

        parser.add_argument('--os-password',
            metavar='<auth-password>',
            default=env('OS_PASSWORD', 'NOVA_PASSWORD'),
            help='Defaults to env[OS_PASSWORD].')

        parser.add_argument('--os-tenant-name',
            metavar='<auth-tenant-name>',
            default=env('OS_TENANT_NAME', 'NOVA_PROJECT_ID'),
            help='Defaults to env[OS_TENANT_NAME].')

        parser.add_argument('--os-tenant-id',
            metavar='<auth-tenant-id>',
            default=env('OS_TENANT_ID'),
            help='Defaults to env[OS_TENANT_ID].')

        parser.add_argument('--os-auth-url',
            metavar='<auth-url>',
            default=env('OS_AUTH_URL', 'NOVA_URL'),
            help='Defaults to env[OS_AUTH_URL].')

        parser.add_argument('--os-cacert',
            metavar='<ca-certificate>',
            default=env('OS_CACERT', default=None),
            help='Specify a CA bundle file to use in '
                 'verifying a TLS (https) server certificate. '
                 'Defaults to env[OS_CACERT]')

        parser.add_argument('--insecure',
            default=env('NOVACLIENT_INSECURE', default=False),
            action='store_true',
            help="Explicitly allow novaclient to perform \"insecure\" "
                 "SSL (https) requests. The server's certificate will "
                 "not be verified against any certificate authorities. "
                 "This option should be used with caution.")


SUPPORTED_MIDDLEWARE = {
    'OpenStack': OpenStackProvider,
}


def env(*args, **kwargs):
    """
    returns the first environment variable set
    if none are non-empty, defaults to '' or keyword arg default
    """
    for arg in args:
        value = os.environ.get(arg, None)
        if value:
            return value
    return kwargs.get('default', '')


def parse_args():
    parser = parser = argparse.ArgumentParser(
        description='Cloud BDII provider')

    parser.add_argument('--middleware',
        metavar='MIDDLEWARE',
        choices=SUPPORTED_MIDDLEWARE,
        default=None,
        help=('Middleware used. Only the following middlewares are '
              'supported: %s. If you do not specify anything, static '
              'values will be used.' % SUPPORTED_MIDDLEWARE.keys()))

    for provider_name, provider in SUPPORTED_MIDDLEWARE.items():
        group = parser.add_argument_group("%s provider options" %
                                          provider_name)
        provider.populate_parser(group)

    return parser.parse_args()


def main():
    args = parse_args()

    if args.middleware:
        dynamic_provider = SUPPORTED_MIDDLEWARE[args.middleware](args)
        images = dynamic_provider.get_images()
        if images:
            provider["os_tpl"] = images
        flavors = dynamic_provider.get_templates()
        if flavors:
            provider['resource_tpl'] = flavors

    bdii = CloudBDII(provider)
    print bdii.render()


if __name__ == "__main__":
    main()
