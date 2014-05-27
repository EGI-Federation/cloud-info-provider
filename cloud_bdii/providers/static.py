import copy
import sys

import yaml

from cloud_bdii import providers


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
                print >> sys.stderr, ('ERROR: missing field %s on '
                                      '"%s" section' % (field, prefix))
                sys.exit(1)
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
            for e, e_data in data[which].iteritems():
                if e == 'defaults':
                    continue
                r = self._get_fields_and_prefix(fields,
                                                prefix,
                                                e_data,
                                                defaults=defaults)
#                r['endpoint_url'] = e
                ret[which][e] = r

        return ret

    def get_site_info(self):
        data = self.yaml['site']

        fields = ('name', 'production_level')
        site_info = self._get_fields_and_prefix(fields, 'site_', data)

        if self.opts.full_bdii_ldif:
            fields = ('url', 'ngi', 'country', 'latitude', 'longitude',
                      'general_contact', 'sysadmin_contact',
                      'security_contact', 'user_support_contact',
                      'bdii_host', 'bdii_port')
            r = self._get_fields_and_prefix(fields, 'site_', data)
            site_info.update(r)

        return site_info

    def get_images(self):
        fields = ('name', 'version', 'marketplace_id', 'os_family', 'os_name',
                  'os_version', 'platform')
        images = self._get_what('compute',
                                'images',
                                None,
                                fields,
                                prefix='image_')
        return images['images']

    def get_templates(self):
        fields = ('platform', 'network', 'memory', 'cpu')
        templates = self._get_what('compute',
                                   'templates',
                                   None,
                                   fields,
                                   prefix='template_')

        return templates['templates']

    def get_compute_endpoints(self):
        global_fields = ('total_ram', 'total_cores', 'capabilities',
                         'hypervisor', 'hypervisor_version',
                         'middleware', 'middleware_version',
                         'middleware_developer')
        endpoint_fields = ('api_type', 'api_version',
                           'api_endpoint_technology', 'api_authn_method')
        endpoints = self._get_what('compute',
                                   'endpoints',
                                   global_fields,
                                   endpoint_fields)
        return endpoints

    def get_storage_endpoints(self):
        global_fields = ('total_storage', 'capabilities', 'middleware',
                         'middleware_version', 'middleware_developer')
        endpoint_fields = ('api_type', 'api_version',
                           'api_endpoint_technology',
                           'api_authn_method')

        endpoints = self._get_what('storage',
                                   'endpoints',
                                   global_fields,
                                   endpoint_fields)
        return endpoints

    def _get_defaults(self, what, which):
        try:
            defaults = self.yaml[what][which]['defaults']
        except KeyError:
            return {}
        else:
            if defaults is None:
                return {}
            return copy.deepcopy(defaults)

    def get_image_defaults(self):
        return self._get_defaults('compute', 'images')

    def get_template_defaults(self):
        return self._get_defaults('compute', 'templates')

    def get_compute_endpoint_defaults(self):
        return self._get_defaults('compute', 'endpoint')

    def get_storage_endpoint_defaults(self):
        return self._get_defaults('storage', 'endpoint')
