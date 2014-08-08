#!/usr/bin/env python

import argparse
import os.path

import cloud_bdii.providers.openstack
import cloud_bdii.providers.opennebula
import cloud_bdii.providers.opennebularocci
import cloud_bdii.providers.static

SUPPORTED_MIDDLEWARE = {
    'openstack': cloud_bdii.providers.openstack.OpenStackProvider,
    'opennebula': cloud_bdii.providers.opennebula.OpenNebulaProvider,
    'opennebularocci':
        cloud_bdii.providers.opennebularocci.OpenNebulaROCCIProvider,
    'static': cloud_bdii.providers.static.StaticProvider,
}


class BaseBDII(object):
    templates = ()

    def __init__(self, opts):
        self.opts = opts

        if (opts.middleware != 'static' and
                opts.middleware in SUPPORTED_MIDDLEWARE):
            self.dynamic_provider = SUPPORTED_MIDDLEWARE[opts.middleware](opts)
        else:
            self.dynamic_provider = None

        self.static_provider = SUPPORTED_MIDDLEWARE['static'](opts)

        self.ldif = {}
        for tpl in self.templates:
            template_file = os.path.join(self.opts.template_dir,
                                         '%s.ldif' % tpl)
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
    templates = ('storage_service', 'storage_endpoint', 'storage_capacity')

    def render(self):
        output = []

        endpoints = self._get_info_from_providers('get_storage_endpoints')

        if not endpoints:
            return ''

        site_info = self._get_info_from_providers('get_site_info')
        static_storage_info = dict(endpoints, **site_info)
        static_storage_info.pop('endpoints')

        output.append(self._format_template('storage_service',
                                            static_storage_info))

        for url, endpoint in endpoints['endpoints'].iteritems():
            endpoint.setdefault('endpoint_url', url)
            output.append(self._format_template('storage_endpoint',
                                                endpoint,
                                                extra=static_storage_info))

        output.append(self._format_template('storage_capacity',
                                            static_storage_info))

        return '\n'.join(output)


class ComputeBDII(BaseBDII):
    templates = ('compute_service', 'compute_endpoint',
                 'execution_environment', 'application_environment')

    def render(self):
        output = []
        endpoints = self._get_info_from_providers('get_compute_endpoints')

        if not endpoints['endpoints']:
            return ''

        site_info = self._get_info_from_providers('get_site_info')
        static_compute_info = dict(endpoints, **site_info)
        static_compute_info.pop('endpoints')

        output.append(self._format_template('compute_service',
                                            static_compute_info))

        for url, endpoint in endpoints['endpoints'].iteritems():
            endpoint.setdefault('endpoint_url', url)
            output.append(self._format_template('compute_endpoint',
                                                endpoint,
                                                extra=static_compute_info))

        templates = self._get_info_from_providers('get_templates')
        for tid, ex_env in templates.iteritems():
            ex_env.setdefault('template_id', tid)
            output.append(self._format_template('execution_environment',
                                                ex_env,
                                                extra=site_info))

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
                                                extra=site_info))

        return '\n'.join(output)


class CloudBDII(BaseBDII):
    templates = ('headers', 'domain', 'bdii', 'clouddomain')

    def __init__(self, *args):
        super(CloudBDII, self).__init__(*args)

        if not self.opts.full_bdii_ldif:
            self.templates = ('clouddomain', )

    def render(self):
        output = []
        info = self._get_info_from_providers('get_site_info')

        for tpl in self.templates:
            output.append(self._format_template(tpl, info))

        return '\n'.join(output)


def parse_opts():
    parser = parser = argparse.ArgumentParser(
        description='Cloud BDII provider',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        fromfile_prefix_chars='@')

    parser.add_argument(
        '--yaml-file',
        default='etc/bdii.yaml',
        help=('Path to the YAML file containing configuration static values. '
              'This file will be used to populate the information '
              'to the static provider. These values will be used whenever '
              'a dynamic provider is used and it is not able to produce any '
              'of the required values, or when using the static provider. '))

    parser.add_argument(
        '--template-dir',
        default='etc/templates',
        help=('Path to the directory containing the needed templates'))

    parser.add_argument(
        '--full-bdii-ldif',
        action='store_true',
        default=False,
        help=('Whether to generate a LDIF containing all the '
              'BDII information, or just this node\'s information'))

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

    for cls_ in (CloudBDII, ComputeBDII, StorageBDII):
        bdii = cls_(opts)
        print bdii.render()

if __name__ == '__main__':
    main()
