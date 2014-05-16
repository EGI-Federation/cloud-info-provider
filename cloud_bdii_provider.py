#!/usr/bin/env python

import argparse

import providers.openstack
import providers.static

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


SUPPORTED_MIDDLEWARE = {
    'OpenStack': providers.openstack.OpenStackProvider,
    'static': providers.static.StaticProvider
}


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

    dynamic_provider = SUPPORTED_MIDDLEWARE.get(
        args.middleware, SUPPORTED_MIDDLEWARE['static'])(args)

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
