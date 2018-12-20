import abc
import argparse
import itertools
import six

from cloud_info_provider import exceptions
from cloud_info_provider import importutils

from stevedore import driver


SUPPORTED_MIDDLEWARE = {
    'openstack': 'cloud_info_provider.providers.openstack.OpenStackProvider',
    'opennebula': 'cloud_info_provider.providers.opennebula.'
                  'OpenNebulaProvider',
    'opennebularocci': 'cloud_info_provider.providers.opennebula.'
                       'OpenNebulaROCCIProvider',
    'static': 'cloud_info_provider.providers.static.StaticProvider',
    'ooi': 'cloud_info_provider.providers.ooi.OoiProvider',
}


@six.add_metaclass(abc.ABCMeta)
class BaseFetcher(object):
    def __init__(self, opts):
        self.opts = opts

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

    def _get_info_from_providers(self, method, **provider_kwargs):
        info = {}
        for i in (self.static_provider, self.dynamic_provider):
            if not i:
                continue
            result = getattr(i, method)(**provider_kwargs)
            info.update(result)
        return info

    @abc.abstractmethod
    def fetch(self):
        """Fetch information from the resource type."""


class StorageFetcher(BaseFetcher):
    def __init__(self, opts):
        super(StorageFetcher, self).__init__(opts)

        self.templates = ['storage']

    def fetch(self):
        endpoints = self._get_info_from_providers('get_storage_endpoints')

        if not endpoints.get('endpoints'):
            return {}

        site_info = self._get_info_from_providers('get_site_info')
        static_storage_info = dict(endpoints, **site_info)
        static_storage_info.pop('endpoints')

        for endpoint in endpoints['endpoints'].values():
            endpoint.update(static_storage_info)

        info = {}
        info.update({'endpoints': endpoints})
        info.update({'static_storage_info': static_storage_info})

        return info


class ComputeFetcher(BaseFetcher):
    def __init__(self, opts):
        super(ComputeFetcher, self).__init__(opts)
        self.templates = ['compute']

    def fetch(self):
        info = {}

        # Retrieve global site information
        # XXX Validate if really project agnostic
        # XXX Here it uses the "default" project from the CLI parameters
        site_info = self._get_info_from_providers('get_site_info')

        # Get shares / projects and related images and templates
        shares = self._get_info_from_providers('get_compute_shares')

        for share in shares.values():
            kwargs = share.copy()

            endpoints = self._get_info_from_providers('get_compute_endpoints',
                                                      **kwargs)
            if not endpoints.get('endpoints'):
                return ''

            # Collect static information for endpoints
            static_compute_info = dict(endpoints, **site_info)
            static_compute_info.pop('endpoints')

            # Collect dynamic information
            images = self._get_info_from_providers('get_images',
                                                   **kwargs)
            templates = self._get_info_from_providers('get_templates',
                                                      **kwargs)
            instances = self._get_info_from_providers('get_instances',
                                                      **kwargs)
            quotas = self._get_info_from_providers('get_compute_quotas',
                                                   **kwargs)

            # Add same static information to endpoints, images and templates
            for d in itertools.chain(endpoints['endpoints'].values(),
                                     templates.values(),
                                     images.values()):
                d.update(static_compute_info)

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

        return info


class CloudFetcher(BaseFetcher):
    def __init__(self, opts):
        super(CloudFetcher, self).__init__(opts)
        self.templates = ('headers', 'clouddomain')

    def fetch(self):
        return self._get_info_from_providers('get_site_info')


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
        'format',
        nargs='?',
        default='glue',
        choices=['glue', 'cmdb'],
        help=('Selects the output format'))

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

    mgr = driver.DriverManager(
        namespace='cip.formatters',
        name=opts.format,
        invoke_on_load=True,
    )
    mgr.driver.format(opts)


if __name__ == '__main__':
    main()
