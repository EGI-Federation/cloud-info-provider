import copy
import sys

import yaml

from cloud_bdii import providers

static_info = {}

static_info['os_tpl'] = (
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

static_info['resource_tpl'] = (
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


class StaticProvider(providers.BaseProvider):
    def __init__(self, *args):
        super(StaticProvider, self).__init__(*args)

        self._load_yaml(self.opts.yaml_file)

    def _load_yaml(self, yaml_file):
        with open(yaml_file, "r") as f:
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
            ret["%s%s" % (prefix, field)] = d[field]
        return ret

    def _get_endpoints(self, type_, global_fields, endpoint_fields):
        if type_ not in self.yaml:
            return {}

        endpoints = {"endpoints": {}}

        data = copy.deepcopy(self.yaml[type_])
        r = self._get_fields_and_prefix(global_fields, "%s_" % type_, data)
        endpoints.update(r)

        if "endpoints" in data:
            defaults = data.pop("defaults", {})
            for e, e_data in data["endpoints"].iteritems():
                r = self._get_fields_and_prefix(endpoint_fields,
                                                "%s_" % type_,
                                                e_data,
                                                defaults=defaults)
                r["endpoint_url"] = e
                endpoints["endpoints"][e] = r
        return endpoints

    def get_site_info(self):
        data = self.yaml["site"].copy()

        fields = ("name", "production_level")
        site_info = self._get_fields_and_prefix(fields, "site_", data)

        if self.opts.full_bdii_ldif:
            fields = ('url', 'ngi', 'country', 'latitude', 'longitude',
                      'general_contact', 'sysadmin_contact',
                      'security_contact', 'user_support_contact',
                      'bdii_host', 'bdii_port')
            r = self._get_fields_and_prefix(fields, "site_", data)
            site_info.update(r)

        return site_info

    def get_images(self):
        return static_info.get("os_tpl", [])

    def get_templates(self):
        return static_info.get("resource_tpl", [])

    def get_compute_endpoints(self):
        global_fields = ('total_ram','total_cores', 'capabilities', 'hypervisor',
                         'hypervisor_version', 'middleware', 'middleware_version',
                         'middleware_developer')
        endpoint_fields = ('api_type', 'api_version', 'api_endpoint_technology',
                           'api_authn_method')
        endpoints = self._get_endpoints("compute", global_fields, endpoint_fields)
        return endpoints

    def get_storage_endpoints(self):
        global_fields = ('total_storage', 'capabilities', 'middleware',
                         'middleware_version', 'middleware_developer')
        endpoint_fields = ('api_type', 'api_version', 'api_endpoint_technology',
                           'api_authn_method')

        endpoints = self._get_endpoints("storage", global_fields, endpoint_fields)
        return endpoints
