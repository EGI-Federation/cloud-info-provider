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

        # FIXME(aloga): this is hardcoded
        self._load_yaml(self.opts.yaml_file)

        self.site_info = {}
        self.compute_endpoints = {}
        self.storage_endpoints = {}
        self.flavors = {}
        self.images = {}

        self._load_site_info()
        self._load_compute_endpoint_info()

        self._load_storage_endpoint_info()

    def _load_yaml(self, yaml_file):
        with open(yaml_file, "r") as f:
            self.yaml = yaml.safe_load(f)

    def _format_fields_with_prefix(self, fields, prefix, ydata):
        if ydata is None:
            ydata = self.yaml

        ret = {}
        for field in fields:
            if field not in ydata:
                print >> sys.stderr, ('ERROR: missing field %s on '
                                      '"%s" section' % (field, prefix))
                sys.exit(1)

            ret["%s%s" % (prefix, field)] = ydata[field]
        return ret

    def _load_site_info(self):
        fields = ("name", "production_level")
        r = self._format_fields_with_prefix(fields, "site_",
                                            self.yaml["site"])
        self.site_info.update(r)

        if self.opts.full_bdii_ldif:
            fields = ('url', 'ngi', 'country', 'latitude', 'longitude',
                      'general_contact', 'sysadmin_contact',
                      'security_contact', 'user_support_contact',
                      'bdii_host', 'bdii_port')
            r = self._format_fields_with_prefix(fields, "site_",
                                                self.yaml["site"])
            self.site_info.update(r)

    def _load_storage_endpoint_info(self):
        if "storage" not in self.yaml:
            return

        self.storage_endpoints["endpoints"] = {}

        fields = ('total_storage', 'capabilities', 'middleware',
                  'middleware_version', 'middleware_developer')
        r = self._format_fields_with_prefix(fields, "storage_",
                                            self.yaml["storage"])
        self.storage_endpoints.update(r)

        if "endpoints" in self.yaml["storage"]:
            for e, e_data in self.yaml["storage"]["endpoints"].iteritems():
                fields = ('api_type', 'api_version',
                          'api_endpoint_technology', 'api_authn_method')
                r = self._format_fields_with_prefix(fields,
                                                    "storage_",
                                                    e_data)
                r["endpoint_url"] = e
                self.storage_endpoints["endpoints"][e] = r

    def _load_compute_endpoint_info(self):
        if "compute" not in self.yaml:
            return

        self.compute_endpoints["endpoints"] = {}

        fields = ('total_ram','total_cores', 'capabilities', 'hypervisor',
                  'hypervisor_version', 'middleware', 'middleware_version',
                  'middleware_developer')
        r = self._format_fields_with_prefix(fields,
                                            "compute_",
                                            self.yaml["compute"])
        self.compute_endpoints.update(r)

        if "endpoints" in self.yaml["compute"]:
            for e, e_data in self.yaml["compute"]["endpoints"].iteritems():
                fields = ('api_type', 'api_version', 'api_endpoint_technology',
                          'api_authn_method')
                r = self._format_fields_with_prefix(fields,
                                                    "compute_",
                                                    e_data)
                r["endpoint_url"] = e
                self.compute_endpoints["endpoints"][e] = r

        self._load_flavors()
        self._load_images()

    def _load_flavors(self):
        self.flavors = static_info.get("resource_tpl", [])

    def _load_images(self):
        self.images = static_info.get("os_tpl", [])

    def get_site_info(self):
        return self.site_info

    def get_images(self):
        return self.images

    def get_templates(self):
        return self.flavors

    def get_compute_endpoints(self):
        return self.compute_endpoints

    def get_storage_endpoints(self):
        return self.storage_endpoints
