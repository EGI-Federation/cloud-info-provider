import copy
import re
import socket

import yaml

from cloud_info_provider import exceptions
from cloud_info_provider import providers


class StaticProvider(providers.BaseProvider):
    def __init__(self, *args):
        super(StaticProvider, self).__init__(*args)

        self._load_yaml(self.opts.yaml_file)

    def _load_yaml(self, yaml_file):
        with open(yaml_file, 'r') as f:
            self.yaml = yaml.safe_load(f)

    def _get_fields_and_prefix(self, fields, prefix, data, defaults={}):
        if data is None:
            data = self.yaml

        ret = {}
        d = copy.deepcopy(defaults)
        d.update(data)

        for field in fields:
            if field not in d:
                # This should raise a warning
                d[field] = None
            ret['%s%s' % (prefix, field)] = d[field]
        return ret

    def _get_what(self, what, which, g_fields, fields, prefix=None):
        if what not in self.yaml:
            return {}

        if prefix is None:
            prefix = '%s_' % what

        ret = {which: {}}

        data = self.yaml[what]
        if g_fields is not None:
            r = self._get_fields_and_prefix(g_fields, '%s_' % what, data)
            ret.update(r)

        if which in data:
            defaults = self._get_defaults(what, which)
            for e, e_data in data[which].items():
                if e == 'defaults':
                    continue
                r = self._get_fields_and_prefix(fields,
                                                prefix,
                                                e_data,
                                                defaults=defaults)
                ret[which][e] = r

        return ret

    def _get_suffix(self, site_info):
        if self.opts.site_in_suffix:
            return ('GLUE2DomainID=%(site_name)s,o=glue' %
                    {'site_name': site_info['site_name']})
        else:
            return 'o=glue'

    def _get_site_info_from_bdii_conf(self):
        try:
            with open(self.opts.glite_site_info_static, 'r') as f:
                for line in f.readlines():
                    m = re.search('^SITE_NAME *= *(.*)$', line)
                    if m:
                        return m.group(1)
        except Exception:
            raise exceptions.StaticProviderException(
                'Cannot find site name. '
                'Specify one in the YAML site configuration or be '
                'sure the file %s is'
                'accessible and readable' % self.opts.glite_site_info_static)

    def get_site_info(self, **kwargs):
        data = self.yaml.get('site', {'name': None})
        site_info = self._get_fields_and_prefix(('name', ), 'site_', data)

        # Resolve site name from BDII configuration
        if site_info['site_name'] is None:
            site_info['site_name'] = self._get_site_info_from_bdii_conf()

        site_info['suffix'] = self._get_suffix(site_info)

        return site_info

    def get_images(self, **kwargs):
        fields = ('name', 'id', 'native_id', 'description', 'version',
                  'marketplace_id', 'platform',
                  'os_family', 'os_name', 'os_version',
                  'minimal_cpu', 'recommended_cpu',
                  'minimal_ram', 'recommended_ram',
                  'minimal_accel', 'recommended_accel', 'accel_type',
                  'traffic_in', 'traffic_out', 'access_info',
                  'context_format', 'software')
        images = self._get_what('compute',
                                'images',
                                None,
                                fields,
                                prefix='image_')
        return images['images']

    def get_templates(self, **kwargs):
        fields = ('platform', 'network', 'network_in', 'network_out',
                  'memory', 'ephemeral', 'disk', 'cpu')
        templates = self._get_what('compute',
                                   'templates',
                                   None,
                                   fields,
                                   prefix='template_')
        return templates['templates']

    def get_instances(self, **kwargs):
        fields = ('name', 'image_id', 'template_id', 'status')
        instances = self._get_what('compute',
                                   'instances',
                                   None,
                                   fields,
                                   prefix='instance_')
        return instances['instances']

    def get_compute_shares(self, **kwargs):
        fields = ('instance_max_cpu', 'instance_max_ram',
                  'instance_max_accelerators',
                  'auth', 'sla', 'network_info', 'membership')
        shares = self._get_what('compute',
                                'shares',
                                None,
                                fields,
                                prefix='')
        return shares['shares']

    def get_compute_quotas(self, **kwargs):
        fields = ('instances', 'cores', 'ram',
                  'floating_ips', 'fixed_ips', 'metadata_items',
                  'injected_files', 'injected_file_content_bytes',
                  'injected_file_path_bytes', 'key_pairs',
                  'security_groups', 'security_group_rules',
                  'server_groups', 'server_group_members')
        quotas = self._get_what('compute',
                                'quotas',
                                None,
                                fields,
                                prefix='compute_')
        return quotas['quotas']

    def get_compute_endpoints(self, **kwargs):
        global_fields = ('service_production_level', 'total_ram',
                         'total_cores', 'capabilities',
                         'hypervisor', 'hypervisor_version',
                         'virtual_disk_formats',
                         'max_dedicated_ram', 'min_dedicated_ram',
                         'max_accelerators', 'min_accelerators',
                         'total_accelerators', 'accelerators_virt_type',
                         'network_virt_type', 'cpu_virt_type',
                         'failover', 'live_migration', 'vm_backup_restore',
                         'service_name')
        endpoint_fields = ('production_level', 'api_type', 'api_version',
                           'api_endpoint_technology', 'api_authn_method',
                           'endpoint_url',
                           'middleware', 'middleware_developer',
                           'middleware_version',
                           'occi_api_version',
                           'occi_middleware_version')
        endpoints = self._get_what('compute',
                                   'endpoints',
                                   global_fields,
                                   endpoint_fields)
        if endpoints and not endpoints.get('compute_service_name'):
            endpoints['compute_service_name'] = socket.getfqdn()
        return endpoints

    def get_storage_endpoints(self, **kwargs):
        global_fields = ('service_production_level', 'total_storage',
                         'capabilities', 'middleware',
                         'middleware_version', 'middleware_developer',
                         'service_name')
        endpoint_fields = ('production_level', 'api_type', 'api_version',
                           'api_endpoint_technology',
                           'api_authn_method')

        endpoints = self._get_what('storage',
                                   'endpoints',
                                   global_fields,
                                   endpoint_fields)
        if endpoints and not endpoints.get('compute_service_name'):
            endpoints['storage_service_name'] = socket.getfqdn()
        return endpoints

    def _get_defaults(self, what, which, prefix=''):
        try:
            defaults = self.yaml[what][which]['defaults']
        except KeyError:
            return {}

        if defaults is None:
            return {}

        if prefix:
            aux = {}
            for k, v in defaults.items():
                key = '%s%s' % (prefix, k)
                aux[key] = v
            defaults = aux

        return copy.deepcopy(defaults)

    def get_image_defaults(self, prefix=False):
        prefix = 'image_' if prefix else ''
        return self._get_defaults('compute', 'images', prefix=prefix)

    def get_template_defaults(self, prefix=False):
        prefix = 'template_' if prefix else ''
        return self._get_defaults('compute', 'templates', prefix=prefix)

    def get_compute_endpoint_defaults(self, prefix=False):
        prefix = 'compute_' if prefix else ''
        return self._get_defaults('compute', 'endpoints', prefix=prefix)

    def get_compute_quotas_defaults(self, prefix=False):
        prefix = 'compute_' if prefix else ''
        return self._get_defaults('compute', 'quotas', prefix=prefix)

    def get_storage_endpoint_defaults(self, prefix=False):
        prefix = 'storage_' if prefix else ''
        return self._get_defaults('storage', 'endpoints', prefix=prefix)

    @staticmethod
    def populate_parser(parser):
        parser.add_argument(
            '--glite-site-info-static',
            metavar='<glite-site-info-static>',
            default='/etc/glite-info-static/site/site.cfg',
            help='Fallback file where the site name is stored.')

        return parser
