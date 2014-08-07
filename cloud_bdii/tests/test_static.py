import unittest
import os.path

from cloud_bdii.providers import static as static_provider


class StaticProviderTest(unittest.TestCase):
    def setUp(self):
        class Opts(object):
            yaml_file = None
            full_bdii_ldif = False

        cwd = os.path.dirname(__file__)
        yaml_file = os.path.join(cwd, "..", "..", "etc", "sample.static.yaml")

        self.opts = Opts()
        self.opts.yaml_file = yaml_file
        self.provider = static_provider.StaticProvider(self.opts)

    def test_get_fields(self):
        cases = (
            (
                ['bar', 'baz', 'foobar'],  # fields
                '',  # prefix
                {'bar': 1, 'baz': 2, 'bazonk': 3},  # data
                {},  # yaml
                {},  # defaults
                {'bar': 1, 'foobar': None, 'baz': 2}  # expected
            ),
            (
                ['bar', 'baz', 'foobar'],
                'foo_',
                {'bar': 1, 'baz': 2, 'bazonk': 3},
                {},
                {},
                {'foo_bar': 1, 'foo_foobar': None, 'foo_baz': 2}
            ),
            (
                ['bar', 'baz', 'foobar'],
                'foo_',
                None,
                {'bar': 1, 'baz': 2, 'bazonk': 3},
                {},
                {'foo_bar': 1, 'foo_foobar': None, 'foo_baz': 2}
            ),
            (
                ['bar', 'baz', 'foobar'],
                'foo_',
                {'bar': 1, 'baz': 2, 'bazonk': 3},
                {},
                {'foobar': 'barfoo'},
                {'foo_bar': 1, 'foo_foobar': 'barfoo', 'foo_baz': 2}
            ),
        )
        for fields, prefix, data, yaml, defaults, expected in cases:
            self.provider.yaml = yaml
            ret = self.provider._get_fields_and_prefix(fields,
                                                       prefix,
                                                       data,
                                                       defaults=defaults)
            self.assertEqual(expected, ret)

    def test_get_defaults(self):
        cases = (
            (
                'foo',  # what
                'bar',  # which
                '',  # prefix
                {},  # yaml
                {},  # expected
            ),
            (
                'foo',
                'bar',
                '',
                {'foo': {'bar': {'defaults': None}}},
                {},
            ),
            (
                'foo',
                'bar',
                '',
                {'foo': {'bar': {'defaults': {'foobar': 'barfoo'}}}},
                {'foobar': 'barfoo'},
            ),
            (
                'foo',
                'bar',
                'brink_',
                {'foo': {'bar': {'defaults': {'foobar': 'barfoo'}}}},
                {'brink_foobar': 'barfoo'},
            ),
        )
        for what, which, prefix, yaml, expected in cases:
            self.provider.yaml = yaml
            ret = self.provider._get_defaults(what, which, prefix=prefix)
            self.assertEqual(expected, ret)

    def test_get_what(self):
        cases = (
            (
                'foo',  # What
                None,  # which
                None,  # g_fields
                None,  # fields
                None,  # prefix
                {},  # yaml
                {},  # expected
            ),
            (
                'foo',
                'bar',
                None,
                None,
                None,
                {'foo': {}},
                {'bar': {}},
            ),
            (
                'foo',
                'bar',
                None,
                ['bazonk'],
                None,
                {'foo': {'bar': {'baz': {'bazonk': 1}}}},
                {'bar': {'baz': {'foo_bazonk': 1}}}
            ),
            (
                'foo',
                'bar',
                ['bronk'],
                ['bazonk'],
                None,
                {'foo': {'bronk': 'brink', 'bar': {'baz': {'bazonk': 1}}}},
                {'bar': {'baz': {'foo_bazonk': 1}}, 'foo_bronk': 'brink'}
            ),
        )
        for what, which, g_fields, fields, prefix, yaml, expected in cases:
            self.provider.yaml = yaml
            ret = self.provider._get_what(what,
                                          which,
                                          g_fields,
                                          fields,
                                          prefix=prefix)
            self.assertEqual(expected, ret)

    def test_get_image_defaults(self):
        yaml = {'compute': {'images': {'defaults': {'foo': 'bar',
                                                    'baz': 'bazonk'}}}}
        self.provider.yaml = yaml
        self.assertEqual({'foo': 'bar', 'baz': 'bazonk'},
                         self.provider.get_image_defaults())
        self.assertEqual({'image_foo': 'bar', 'image_baz': 'bazonk'},
                         self.provider.get_image_defaults(prefix=True))

    def test_get_template_defaults(self):
        yaml = {'compute': {'templates': {'defaults': {'foo': 'bar',
                                                       'baz': 'bazonk'}}}}
        self.provider.yaml = yaml
        self.assertEqual({'foo': 'bar', 'baz': 'bazonk'},
                         self.provider.get_template_defaults())
        self.assertEqual({'template_foo': 'bar', 'template_baz': 'bazonk'},
                         self.provider.get_template_defaults(prefix=True))

    def test_get_compute_endpoint_defaults(self):
        yaml = {'compute': {'endpoints': {'defaults': {'foo': 'bar',
                                                       'baz': 'bazonk'}}}}
        self.provider.yaml = yaml
        self.assertEqual({'foo': 'bar', 'baz': 'bazonk'},
                         self.provider.get_compute_endpoint_defaults())
        self.assertEqual(
            {'compute_foo': 'bar', 'compute_baz': 'bazonk'},
            self.provider.get_compute_endpoint_defaults(prefix=True)
        )

    def test_get_storage_endpoint_defaults(self):
        yaml = {'storage': {'endpoints': {'defaults': {'foo': 'bar',
                                                       'baz': 'bazonk'}}}}
        self.provider.yaml = yaml
        self.assertEqual({'foo': 'bar', 'baz': 'bazonk'},
                         self.provider.get_storage_endpoint_defaults())
        self.assertEqual(
            {'storage_foo': 'bar', 'storage_baz': 'bazonk'},
            self.provider.get_storage_endpoint_defaults(prefix=True)
        )

    def test_get_storage_endpoints(self):
        expected = {
            'endpoints': {
                'https://storage-service01.example.org:8080': {
                    'storage_api_authn_method': 'X509-VOMS',
                    'storage_api_endpoint_technology': 'REST',
                    'storage_api_type': 'CDMI',
                    'storage_api_version': '1.0.1'
                },
                'https://storage-service02.example.org:8080': {
                    'storage_api_authn_method': 'X509-VOMS',
                    'storage_api_endpoint_technology': 'REST',
                    'storage_api_type': 'CDMI',
                    'storage_api_version': '1.0.1'
                }
            },
            'storage_capabilities': ['cloud.data.upload'],
            'storage_middleware': 'A Middleware',
            'storage_middleware_developer': 'Middleware Developer',
            'storage_middleware_version': 'v1.0',
            'storage_total_storage': 0,
        }
        self.assertEqual(expected, self.provider.get_storage_endpoints())

    def test_get_compute_endpoints(self):
        expected = {
            'compute_capabilities': ['cloud.managementSystem',
                                     'cloud.vm.uploadImage'],
            'compute_hypervisor': 'Foo Hypervisor',
            'compute_hypervisor_version': '0.0.0',
            'compute_middleware': 'A Middleware',
            'compute_middleware_developer': 'Middleware Developer',
            'compute_middleware_version': 'v1.0',
            'compute_total_cores': 0,
            'compute_total_ram': 0,
            'endpoints': {
                'https://cloud-service01.example.org:8787': {
                    'compute_api_authn_method': 'X509-VOMS',
                    'compute_api_endpoint_technology': 'REST',
                    'compute_api_type': 'OCCI',
                    'compute_api_version': 1.1
                },
                'https://cloud-service02.example.org:8787': {
                    'compute_api_authn_method': 'X509',
                    'compute_api_endpoint_technology': 'REST',
                    'compute_api_type': 'OCCI',
                    'compute_api_version': 1.1
                },
                'https://cloud-service03.example.org:8787': {
                    'compute_api_authn_method': 'User/Password',
                    'compute_api_endpoint_technology': 'REST',
                    'compute_api_type': 'OCCI',
                    'compute_api_version': 1.1
                }
            }
        }

        self.assertEqual(expected, self.provider.get_compute_endpoints())

    def test_get_site_info_no_full_bdii(self):
        expected = {
            'site_name': 'SITE_NAME',
            'site_production_level': 'production',
            'suffix': 'o=glue'
        }

        self.provider.opts.full_bdii_ldif = False
        self.assertEqual(expected, self.provider.get_site_info())

    def test_get_site_info_full_bdii(self):
        expected = {
            'site_bdii_host': 'site.bdii.example.org',
            'site_bdii_port': 2170,
            'site_country': 'ES',
            'site_general_contact': 'general-support@example.org',
            'site_latitude': 0.0,
            'site_longitude': 0.0,
            'site_name': 'SITE_NAME',
            'site_ngi': 'NGI_FOO',
            'site_production_level': 'production',
            'site_security_contact': 'security-support@example.org',
            'site_sysadmin_contact': 'support@example.org',
            'site_url': 'http://site.url.example.org/',
            'site_user_support_contact': 'user-support@example.org',
            'suffix': 'GLUE2DomainID=SITE_NAME,o=glue'
        }

        self.provider.opts.full_bdii_ldif = True
        self.assertEqual(expected, self.provider.get_site_info())

    def test_get_images(self):
        expected = {
            'os#foobarid': {
                'image_marketplace_id': (
                    'http://url.to.marketplace.id.example.org/foo/bar'
                ),
                'image_name': 'Foo Image',
                'image_os_family': 'linux',
                'image_os_name': 'Cirros',
                'image_os_version': 1.0,
                'image_platform': 'amd64',
                'image_version': 1.0
            }
        }

        self.assertEqual(expected, self.provider.get_images())

    def test_get_images_with_yaml(self):
        yaml = {
            'compute': {
                'images': {
                    'defaults': {
                        'platform': 'amd64',
                    },
                    'os#fooid': {
                        'name': 'Foo Image',
                        'version': 1.0,
                        'marketplace_id': 'http://example.org/foo',
                        'os_family': 'linux',
                        'os_name': 'Cirros',
                        'os_version': 1.0,
                    },
                    'os#barid': {
                        'name': 'Bar Image',
                        'version': 2.0,
                        'marketplace_id': 'http://example.org/bar',
                        'os_family': 'linux',
                        'os_name': 'Cirros',
                        'os_version': 2.0,
                        'platform': 'i686',
                    },
                }
            }
        }
        expected = {
            'os#barid': {
                'image_marketplace_id': 'http://example.org/bar',
                'image_name': 'Bar Image',
                'image_os_family': 'linux',
                'image_os_name': 'Cirros',
                'image_os_version': 2.0,
                'image_platform': 'i686',
                'image_version': 2.0
            },
            'os#fooid': {
                'image_marketplace_id': 'http://example.org/foo',
                'image_name': 'Foo Image',
                'image_os_family': 'linux',
                'image_os_name': 'Cirros',
                'image_os_version': 1.0,
                'image_platform': 'amd64',
                'image_version': 1.0
            }
        }

        self.provider.yaml = yaml
        self.assertEqual(expected, self.provider.get_images())

    def test_get_templates(self):
        expected = {
            'resource#extra_large': {
                'template_cpu': 8,
                'template_memory': 16384,
                'template_network': 'public',
                'template_platform': 'amd64'
            },
            'resource#large': {
                'template_cpu': 4,
                'template_memory': 8196,
                'template_network': 'public',
                'template_platform': 'amd64'
            },
            'resource#medium': {
                'template_cpu': 2,
                'template_memory': 4096,
                'template_network': 'public',
                'template_platform': 'amd64'
            },
            'resource#small': {
                'template_cpu': 1,
                'template_memory': 1024,
                'template_network': 'public',
                'template_platform': 'amd64'
            }
        }

        self.assertEqual(expected, self.provider.get_templates())
