import argparse
import os.path

from cloud_info import exceptions
from cloud_info import importutils

import mako.template

SUPPORTED_MIDDLEWARE = {
    'openstack': 'cloud_info.providers.openstack.OpenStackProvider',
    'opennebula': 'cloud_info.providers.opennebula.OpenNebulaProvider',
    'indigoon': 'cloud_info.providers.opennebula.IndigoONProvider',
    'opennebularocci': 'cloud_info.providers.opennebula.'
                       'OpenNebulaROCCIProvider',
    'static': 'cloud_info.providers.static.StaticProvider',
}


class BaseBDII(object):
    def __init__(self, opts):
        self.opts = opts

        self.templates = ()
        self.templates_files = {}

        if (opts.middleware != 'static' and
                opts.middleware in SUPPORTED_MIDDLEWARE):
            provider_cls = importutils.import_class(
                SUPPORTED_MIDDLEWARE[opts.middleware]
            )
            self.dynamic_provider = provider_cls(opts)
        else:
            self.dynamic_provider = None

        provider_cls = importutils.import_class(
            SUPPORTED_MIDDLEWARE['static']
        )
        self.static_provider = provider_cls(opts)

    def load_templates(self):
        self.templates_files = {}
        for tpl in self.templates:
            template_extension = self.opts.template_extension
            template_file = os.path.join(self.opts.template_dir,
                                         '%s.%s' % (tpl, template_extension))
            self.templates_files[tpl] = template_file

    def _get_info_from_providers(self, method, provider_opts=None):
        # XXX Temporarily update dynamic provider parameters
        # XXX Required to be able to pass a custom project to the provider
        # XXX to retrieve project-specific templates and images
        if provider_opts:
            opts = self.opts
            d = vars(opts)
            for k, v in provider_opts.items():
                d[k] = v

            provider_cls = importutils.import_class(
                SUPPORTED_MIDDLEWARE[opts.middleware]
            )
            self.dynamic_provider = provider_cls(opts)

        info = {}
        for i in (self.static_provider, self.dynamic_provider):
            if not i:
                continue
            result = getattr(i, method)()
            info.update(result)
        return info

    def _format_template(self, template, info, extra={}):
        info = info.copy()
        info.update(extra)
        t = self.templates_files[template]
        tpl = mako.template.Template(filename=t)
        return tpl.render(attributes=info)


class StorageBDII(BaseBDII):
    def __init__(self, opts):
        super(StorageBDII, self).__init__(opts)

        self.templates = ['storage']

    def render(self):
        endpoints = self._get_info_from_providers('get_storage_endpoints')

        if not endpoints.get('endpoints'):
            return ''

        site_info = self._get_info_from_providers('get_site_info')
        static_storage_info = dict(endpoints, **site_info)
        static_storage_info.pop('endpoints')

        for url, endpoint in endpoints['endpoints'].items():
            endpoint.update(static_storage_info)

        info = {}
        info.update({'endpoints': endpoints})
        info.update({'static_storage_info': static_storage_info})

        return self._format_template('storage', info)


class ComputeBDII(BaseBDII):
    def __init__(self, opts):
        super(ComputeBDII, self).__init__(opts)

        self.templates = ['compute']

    def render(self):
        info = {}

        # Retrieve global site information
        # XXX Validate if really project agnostic
        # XXX Here it uses the "default" project from the CLI parameters
        site_info = self._get_info_from_providers('get_site_info')

        # Get shares / projects and related images and templates
        shares = self._get_info_from_providers('get_compute_shares')

        for share_id, share in shares.items():
            project = share['project']

            endpoints = self._get_info_from_providers('get_compute_endpoints',
                                                      {'os_tenant_name':
                                                          project})

            if not endpoints.get('endpoints'):
                return ''

            # Collect static information for endpoints
            static_compute_info = dict(endpoints, **site_info)
            static_compute_info.pop('endpoints')

            # Add same static information to all endpoints
            for url, endpoint in endpoints['endpoints'].items():
                endpoint.update(static_compute_info)

            images = self._get_info_from_providers('get_images',
                                                   {'os_tenant_name': project})

            templates = self._get_info_from_providers('get_templates',
                                                      {'os_tenant_name':
                                                          project})

            instances = self._get_info_from_providers('get_instances',
                                                      {'os_tenant_name':
                                                          project})

            quotas = self._get_info_from_providers('get_compute_quotas',
                                                   {'os_tenant_name':
                                                       project})

            for template_id, template in templates.items():
                template.update(static_compute_info)

            for image_id, image in images.items():
                image.update(static_compute_info)

            share['images'] = images
            share['templates'] = templates
            share['instances'] = instances
            share['endpoints'] = endpoints
            share['quotas'] = quotas

        # XXX Avoid creating a new list
        endpoints = {endpoint_id: endpoint for share_id, share in
                     shares.items() for endpoint_id,
                     endpoint in share['endpoints'].items()}

        # XXX Avoid redoing what was done in the previous shares loop
        static_compute_info = dict(endpoints, **site_info)
        static_compute_info.pop('endpoints')

        info.update({'static_compute_info': static_compute_info})
        info.update({'shares': shares})

        return self._format_template('compute', info)


class CloudBDII(BaseBDII):
    def __init__(self, opts):
        super(CloudBDII, self).__init__(opts)

        if not self.opts.full_bdii_ldif:
            self.templates = ('headers', 'clouddomain')
        else:
            self.templates = ('headers', 'domain', 'bdii', 'clouddomain')

    def render(self):
        output = []
        info = self._get_info_from_providers('get_site_info')

        for tpl in self.templates:
            output.append(self._format_template(tpl, info))

        return '\n'.join(output)


def parse_opts():
    parser = argparse.ArgumentParser(
        description='Cloud BDII provider',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        fromfile_prefix_chars='@',
        conflict_handler="resolve",
    )

    parser.add_argument(
        '--yaml-file',
        default='/etc/cloud-info-provider/static.yaml',
        help=('Path to the YAML file containing configuration static values. '
              'This file will be used to populate the information '
              'to the static provider. These values will be used whenever '
              'a dynamic provider is used and it is not able to produce any '
              'of the required values, or when using the static provider. '))

    parser.add_argument(
        '--template-dir',
        default='/etc/cloud-info-provider/templates',
        help=('Path to the directory containing the needed templates'))

    parser.add_argument(
        '--template-extension',
        default='ldif',
        help=('Extension to use for the templates'))

    parser.add_argument(
        '--full-bdii-ldif',
        action='store_true',
        default=False,
        help=('Whether to generate a LDIF containing all the '
              'BDII information, or just this node\'s information\n'
              'NOTE: it does not generate GlueSchema 1.3 information'))

    parser.add_argument(
        '--site-in-suffix',
        action='store_true',
        default=False,
        help=('Whether to include the site name in the generated DN\'s'
              'suffix (Use only for execution as a site-BDII provider)'))

    parser.add_argument(
        '--middleware',
        metavar='MIDDLEWARE',
        choices=SUPPORTED_MIDDLEWARE,
        default='static',
        help=('Middleware used. Only the following middlewares are '
              'supported: %s. If you do not specify anything, static '
              'values will be used.' % SUPPORTED_MIDDLEWARE.keys()))

    for provider_name, provider in SUPPORTED_MIDDLEWARE.items():
        group = parser.add_argument_group('%s provider options' %
                                          provider_name)

        # NOTE(aloga): importing the class may fail because of missing
        # dependencies, so we skip those options. This is not the best option,
        # as those options will not be present until the dependencies are
        # satisfied...
        try:
            provider = importutils.import_class(provider)
            provider.populate_parser(group)
        except (exceptions.OpenStackProviderException,
                exceptions.OpenNebulaProviderException):
            pass

    return parser.parse_args()


def main():
    opts = parse_opts()

    for cls_ in (CloudBDII, ComputeBDII, StorageBDII):
        bdii = cls_(opts)
        bdii.load_templates()
        print(bdii.render().encode('utf-8'))

if __name__ == '__main__':
    main()
