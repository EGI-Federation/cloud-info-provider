import argparse
import os.path

import cloud_bdii.providers.opennebula
import cloud_bdii.providers.openstack
import cloud_bdii.providers.static

SUPPORTED_MIDDLEWARE = {
    # 'openstack': cloud_bdii.providers.openstack.OpenStackProvider,
    # 'opennebula': cloud_bdii.providers.opennebula.OpenNebulaProvider,
    'opennebulaindigo': cloud_bdii.providers.opennebula.IndigoONProvider,
    # 'opennebularocci':
    # cloud_bdii.providers.opennebula.OpenNebulaROCCIProvider,
    'static': cloud_bdii.providers.static.StaticProvider,
}


class BaseBDII(object):
    def __init__(self, opts):
        self.opts = opts

        self.templates = ()
        self.ldif = {}

        if (opts.middleware != 'static' and
                opts.middleware in SUPPORTED_MIDDLEWARE):
            self.dynamic_provider = SUPPORTED_MIDDLEWARE[opts.middleware](opts)
        else:
            self.dynamic_provider = None

        self.static_provider = SUPPORTED_MIDDLEWARE['static'](opts)

    def load_templates(self):
        self.ldif = {}
        for tpl in self.templates:
            template_extension = self.opts.template_extension
            template_file = os.path.join(self.opts.template_dir,
                                         '%s.%s' % (tpl, template_extension))
            with open(template_file, 'r') as f:
                self.ldif[tpl] = f.read()

    def _get_info_from_providers(self, method):
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
        return self.ldif.get(template, '') % info


class StorageBDII(BaseBDII):
    def __init__(self, opts):
        super(StorageBDII, self).__init__(opts)

        self.templates = ('storage_service',
                          'storage_endpoint',
                          'storage_capacity')

    def render(self):
        output = []

        endpoints = self._get_info_from_providers('get_storage_endpoints')

        if not endpoints.get('endpoints'):
            return ''

        site_info = self._get_info_from_providers('get_site_info')
        static_storage_info = dict(endpoints, **site_info)
        static_storage_info.pop('endpoints')

        output.append(self._format_template('storage_service',
                                            static_storage_info))

        for url, endpoint in endpoints['endpoints'].items():
            endpoint.setdefault('endpoint_url', url)
            output.append(self._format_template('storage_endpoint',
                                                endpoint,
                                                extra=static_storage_info))

        output.append(self._format_template('storage_capacity',
                                            static_storage_info))

        return '\n'.join(output)


class ComputeBDII(BaseBDII):
    def __init__(self, opts):
        super(ComputeBDII, self).__init__(opts)

        self.templates = ('compute_service',
                          'compute_endpoint',
                          'execution_environment',
                          'application_environment')

    def render(self):
        output = []
        endpoints = self._get_info_from_providers('get_compute_endpoints')

        if not endpoints.get('endpoints'):
            return ''

        site_info = self._get_info_from_providers('get_site_info')
        static_compute_info = dict(endpoints, **site_info)
        static_compute_info.pop('endpoints')

        output.append(self._format_template('compute_service',
                                            static_compute_info))

        for url, endpoint in endpoints['endpoints'].items():
            endpoint.setdefault('endpoint_url', url)
            output.append(self._format_template('compute_endpoint',
                                                endpoint,
                                                extra=static_compute_info))

        templates = self._get_info_from_providers('get_templates')
        for tid, ex_env in templates.items():
            ex_env.setdefault('template_id', tid)
            output.append(self._format_template('execution_environment',
                                                ex_env,
                                                extra=static_compute_info))

        images = self._get_info_from_providers('get_images')
        for iid, app_env in images.items():
            app_env.setdefault('image_id', iid)
            app_env.setdefault('image_description',
                               ('%(image_name)s version '
                                '%(image_version)s on '
                                '%(image_os_family)s %(image_os_name)s '
                                '%(image_os_version)s '
                                '%(image_platform)s' % app_env))
            output.append(self._format_template('application_environment',
                                                app_env,
                                                extra=static_compute_info))

        return '\n'.join(output)


class IndigoComputeBDII(BaseBDII):
    def __init__(self, opts):
        super(IndigoComputeBDII, self).__init__(opts)

        # XXX disable non-required templates
        # self.templates = ('compute_service',
        #                   'compute_endpoint',
        #                   'execution_environment',
        #                   'application_environment')
        self.templates = ('execution_environment',
                          'application_environment')

    def render(self):
        output = []
        endpoints = self._get_info_from_providers('get_compute_endpoints')

        if not endpoints.get('endpoints'):
            return ''

        site_info = self._get_info_from_providers('get_site_info')
        static_compute_info = dict(endpoints, **site_info)
        static_compute_info.pop('endpoints')

        # prepare json formatting
        output.append('{')
        output.append('templates:')
        output.append('[')

        # output.append(self._format_template('compute_service',
        #                                     static_compute_info))

        # for url, endpoint in endpoints['endpoints'].iteritems():
        #     endpoint.setdefault('endpoint_url', url)
        #     output.append(self._format_template('compute_endpoint',
        #                                         endpoint,
        #                                         extra=static_compute_info))

        templates = self._get_info_from_providers('get_templates')
        for tid, ex_env in templates.iteritems():
            ex_env.setdefault('template_id', tid)
            output.append(self._format_template('execution_environment',
                                                ex_env,
                                                extra=static_compute_info))
            output.append(',')
        # XXX remote ending coma if any
        if output[-1] == ',':
            del output[-1]
        output.append(']')
        output.append("},")

        output.append('{')
        output.append('images:')
        output.append('[')

        images = self._get_info_from_providers('get_images')
        for iid, app_env in images.iteritems():
            app_env.setdefault('image_id', iid)
            app_env.setdefault('image_description',
                               ('%(image_name)s version '
                                '%(image_version)s on '
                                '%(image_os_family)s %(image_os_name)s '
                                '%(image_os_version)s '
                                '%(image_platform)s' % app_env))
            output.append(self._format_template('application_environment',
                                                app_env,
                                                extra=static_compute_info))
            output.append(',')

        # XXX remote ending coma if any
        if output[-1] == ',':
            del output[-1]
        # End JSON output
        output.append(']')
        output.append('}')
        return '\n'.join(output)


class CloudBDII(BaseBDII):
    def __init__(self, opts):
        super(CloudBDII, self).__init__(opts)

        if not self.opts.full_bdii_ldif:
            self.templates = ('headers', 'clouddomain', )
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
        default='/etc/cloud-info-provider/bdii.yaml',
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
        default='json',
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
        provider.populate_parser(group)

    return parser.parse_args()


def main():
    opts = parse_opts()

    bdii = IndigoComputeBDII(opts)
    bdii.load_templates()
    print(bdii.render().encode('utf-8'))
    # XXX do not care of legacy stuff
    # for cls_ in (CloudBDII, ComputeBDII, StorageBDII, IndigoComputeBDII):
    #     bdii = cls_(opts)
    #     bdii.load_templates()
    #     print(bdii.render().encode('utf-8'))

if __name__ == '__main__':
    main()
