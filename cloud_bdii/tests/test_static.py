import unittest
import os.path

from cloud_bdii.providers import static as static_provider
from cloud_bdii.tests import data

DATA = data.DATA


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
        for fields, prefix, indata, yaml, defaults, expected in cases:
            self.provider.yaml = yaml
            ret = self.provider._get_fields_and_prefix(fields,
                                                       prefix,
                                                       indata,
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
        expected = DATA.storage_endpoints
        self.assertEqual(expected, self.provider.get_storage_endpoints())

    def test_get_compute_endpoints(self):
        expected = DATA.compute_endpoints
        self.assertEqual(expected, self.provider.get_compute_endpoints())

    def test_get_site_info_no_full_bdii(self):
        expected = DATA.site_info
        self.provider.opts.full_bdii_ldif = False
        self.assertEqual(expected, self.provider.get_site_info())

    def test_get_site_info_full_bdii(self):
        expected = DATA.site_info_full
        self.provider.opts.full_bdii_ldif = True
        self.assertEqual(expected, self.provider.get_site_info())

    def test_get_images(self):
        expected = DATA.compute_images
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
        expected = DATA.compute_templates
        self.assertEqual(expected, self.provider.get_templates())
