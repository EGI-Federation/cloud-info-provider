import os.path

import mock
import six

from cloud_info_provider import exceptions
from cloud_info_provider.providers import static as static_provider
from cloud_info_provider.tests import base
from cloud_info_provider.tests import data

DATA = data.DATA


class StaticProviderTest(base.TestCase):
    def setUp(self):
        super(StaticProviderTest, self).setUp()

        class Opts(object):
            yaml_file = None
            site_in_suffix = False
            glite_site_info_static = "foo"

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

    def test_get_empty_storage_endpoints(self):
        expected = {}
        self.provider.yaml = {}
        self.assertEqual(expected, self.provider.get_storage_endpoints())

    def test_get_empty_compute_endpoints(self):
        expected = {}
        self.provider.yaml = {}
        self.assertEqual(expected, self.provider.get_compute_endpoints())

    def test_get_default_storage_service_name(self):
        self.provider.yaml = {'storage': {'endpoints': {}}}
        with mock.patch('socket.getfqdn') as m_fqdn:
            m_fqdn.return_value = 'foo'
            ep = self.provider.get_storage_endpoints()
            self.assertEqual('foo', ep.get('storage_service_name'))

    def test_get_default_compute_service_name(self):
        self.provider.yaml = {'compute': {'endpoints': {}}}
        with mock.patch('socket.getfqdn') as m_fqdn:
            m_fqdn.return_value = 'foo'
            ep = self.provider.get_compute_endpoints()
            self.assertEqual('foo', ep.get('compute_service_name'))

    def test_get_storage_endpoints(self):
        expected = DATA.storage_endpoints
        with mock.patch('socket.getfqdn') as m_fqdn:
            m_fqdn.return_value = 'example.org'
            self.assertEqual(expected, self.provider.get_storage_endpoints())

    def test_get_compute_endpoints(self):
        expected = DATA.compute_endpoints
        # fill in missing values
        expected.update({
            'compute_accelerators_virt_type': None,
            'compute_network_virt_type': None,
            'compute_cpu_virt_type': None,
            'compute_virtual_disk_formats': None,
        })
        with mock.patch('socket.getfqdn') as m_fqdn:
            m_fqdn.return_value = 'example.org'
            self.assertEqual(expected, self.provider.get_compute_endpoints())

    def test_no_site_name(self):
        self.opts.glite_site_info_static = "This does not exist"
        self.assertRaises(exceptions.StaticProviderException,
                          self.provider.get_site_info)

    def test_get_suffix_default(self):
        site_info = {'site_name': 'SITE_NAME'}
        self.assertEqual("o=glue", self.provider._get_suffix(site_info))

    def test_get_suffix_site_in_suffix(self):
        site_info = {'site_name': 'SITE_NAME'}
        self.provider.opts.site_in_suffix = True
        self.assertEqual("GLUE2DomainID=SITE_NAME,o=glue",
                         self.provider._get_suffix(site_info))

    def test_get_site_info_no(self):
        data = six.StringIO("SITE_NAME = SITE_NAME")
        expected = DATA.site_info
        with mock.patch('cloud_info_provider.providers.static.open',
                        create=True) as m_open:
            m_open.return_value.__enter__ = lambda x: data
            m_open.return_value.__exit__ = mock.Mock()
            self.assertEqual(expected, self.provider.get_site_info())

    def test_get_images(self):
        expected = DATA.compute_images
        # add undefined values
        for img in expected.values():
            for field in ['image_accel_type',
                          'image_access_info',
                          'image_context_format',
                          'image_description',
                          'image_id',
                          'image_minimal_accel',
                          'image_minimal_cpu',
                          'image_minimal_ram',
                          'image_native_id',
                          'image_recommended_accel',
                          'image_recommended_cpu',
                          'image_recommended_ram',
                          'image_software',
                          'image_traffic_in',
                          'image_traffic_out']:
                if field not in img:
                    img[field] = None
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
        for img in expected.values():
            for field in ['image_accel_type',
                          'image_access_info',
                          'image_context_format',
                          'image_description',
                          'image_id',
                          'image_minimal_accel',
                          'image_minimal_cpu',
                          'image_minimal_ram',
                          'image_native_id',
                          'image_recommended_accel',
                          'image_recommended_cpu',
                          'image_recommended_ram',
                          'image_software',
                          'image_traffic_in',
                          'image_traffic_out']:
                if field not in img:
                    img[field] = None
        self.provider.yaml = yaml
        self.assertEqual(expected, self.provider.get_images())

    def test_get_templates(self):
        expected = DATA.compute_templates
        for tpl in expected.values():
            # default values from file
            tpl.update({
                'template_disk': None,
                'template_ephemeral': None,
                'template_network_in': 'undefined',
                'template_network_out': True,
            })
        self.assertEqual(expected, self.provider.get_templates())
