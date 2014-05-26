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
    templates = ()

    def __init__(self, dynamic_provider, static_provider):
        if opts.middleware != "static" and opts.middleware in SUPPORTED_MIDDLEWARE:
            self.dynamic_provider = SUPPORTED_MIDDLEWARE.get(opts.middleware)(opts)
        else:
            self.dynamic_provider = None

        self.ldif = {}
        for tpl in self.templates:
            with open('templates/%s.ldif' % tpl, 'r') as f:
                self.ldif[tpl] = f.read()

    def _get_info_from_providers(self, method):
        info = None
        for i in (self.static_provider, self.dynamic_provider):
            if not i:
                continue
            result = getattr(i, method)()
            if isinstance(info, dict):
                info.update(result)
            else:
                info = result
        return info

    def _format_template(self, template, info, extra={}):
        info = info.copy()
        info.update(extra)
        return self.ldif.get(template, "") % info


class StaaSBDII(BaseBDII):
    templates = ("storage_service", "storage_endpoint", "storage_capacity")

    def render(self):
        output = []

        static_info = self._get_info_from_providers("get_site_info")

        output.append(self._format_template("storage_service", static_info))

        for endpoint in self._get_info_from_providers('get_staas_endpoints'):
            output.append(self._format_template("storage_endpoint",
                                                static_info,
                                                extra=endpoint))

        output.append(self._format_template("storage_capacity",
                                            static_info))

        return "\n".join(output)


class IaaSBDII(BaseBDII):
    templates = ("compute_service", "compute_endpoint",
                 "execution_environment", "application_environment")

    def render(self):
        output = []

        static_info = self._get_info_from_providers("get_site_info")

        output.append(self._format_template("compute_service", static_info))

        endpoints = self._get_info_from_providers("get_iaas_endpoints")
        for endpoint in endpoints:
            output.append(self._format_template("compute_endpoint",
                                                static_info,
                                                extra=endpoint))

        for ex_env in self._get_info_from_providers('get_templates'):
            output.append(self._format_template("execution_environment",
                                                static_info,
                                                extra=ex_env))

        for app_env in self._get_info_from_providers('get_images'):
            app_env.setdefault("image_description",
                               ("%(image_name)s version %(image_version)s on "
                                "%(os_family)s %(os_name)s %(os_version)s "
                                "%(platform)s" % app_env))
            output.append(self._format_template("application_environment",
                                                static_info,
                                                extra=app_env))

        return "\n".join(output)


class CloudBDII(BaseBDII):
    templates = ("headers", "domain", "bdii")

    def __init__(self, *args):
        super(CloudBDII, self).__init__(*args)

    def render(self):
        output = []
        info = self._get_info_from_providers("get_site_info")

        for tpl in self.templates:
            output.append(self._format_template(tpl, info))

        return "\n".join(output)


SUPPORTED_MIDDLEWARE = {
    'OpenStack': providers.openstack.OpenStackProvider,
    'static': providers.static.StaticProvider,
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

    if args.middleware in SUPPORTED_MIDDLEWARE:
        dynamic_provider = SUPPORTED_MIDDLEWARE.get(args.middleware)(args)
    else:
        dynamic_provider = None

    static_provider = providers.static.StaticProvider(args)

    for cls_ in (CloudBDII, IaaSBDII, StaaSBDII):
        bdii = cls_(dynamic_provider, static_provider)
        print bdii.render()


if __name__ == "__main__":
    main()
