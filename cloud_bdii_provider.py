#!/usr/bin/env python

import argparse

import providers.openstack
import providers.static


class BaseBDII(object):
    templates = ()

    def __init__(self, opts):
        self.opts = opts

        if opts.middleware != "static" and opts.middleware in SUPPORTED_MIDDLEWARE:
            self.dynamic_provider = SUPPORTED_MIDDLEWARE.get(opts.middleware)(opts)
        else:
            self.dynamic_provider = None

        self.static_provider = providers.static.StaticProvider(opts)

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

        endpoints = self._get_info_from_providers("get_staas_endpoints")

        if not endpoints:
            return ""

        site_info = self._get_info_from_providers("get_site_info")
        staas_endpoints = self._get_info_from_providers("get_staas_endpoints")
        static_staas_info = dict(staas_endpoints, **site_info)

        output.append(self._format_template("storage_service",
                                            static_staas_info))

        for endpoint in staas_endpoints["endpoints"]:
            output.append(self._format_template("storage_endpoint",
                                                endpoint,
                                                extra=static_staas_info))

        output.append(self._format_template("storage_capacity",
                                            static_staas_info))

        return "\n".join(output)


class IaaSBDII(BaseBDII):
    templates = ("compute_service", "compute_endpoint",
                 "execution_environment", "application_environment")

    def render(self):
        output = []

        endpoints = self._get_info_from_providers("get_iaas_endpoints")

        if not endpoints:
            return ""

        site_info = self._get_info_from_providers("get_site_info")

        iaas_endpoints = self._get_info_from_providers("get_iaas_endpoints")

        static_iaas_info = dict(iaas_endpoints, **site_info)

        output.append(self._format_template("compute_service", static_iaas_info))

        for endpoint in iaas_endpoints["endpoints"]:
            output.append(self._format_template("compute_endpoint",
                                                endpoint,
                                                extra=static_iaas_info))

        for ex_env in self._get_info_from_providers('get_templates'):
            output.append(self._format_template("execution_environment",
                                                ex_env,
                                                extra=site_info))

        for app_env in self._get_info_from_providers('get_images'):
            app_env.setdefault("image_description",
                               ("%(image_name)s version %(image_version)s on "
                                "%(os_family)s %(os_name)s %(os_version)s "
                                "%(platform)s" % app_env))
            output.append(self._format_template("application_environment",
                                                app_env,
                                                extra=site_info))

        return "\n".join(output)


class CloudBDII(BaseBDII):
    templates = ("headers", "domain", "bdii", "clouddomain")

    def __init__(self, *args):
        super(CloudBDII, self).__init__(*args)

        if not self.opts.full_bdii_ldif:
            self.templates = ("clouddomain",)

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


def parse_opts():
    parser = parser = argparse.ArgumentParser(
        description='Cloud BDII provider',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('--full-bdii-ldif',
        action='store_true',
        default=False,
        help=('Whether to generate a LDIF containing all the '
              'BDII information, or just this node\'s information'))

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
    opts = parse_opts()

    for cls_ in (CloudBDII, IaaSBDII, StaaSBDII):
        bdii = cls_(opts)
        print bdii.render()


if __name__ == "__main__":
    main()
