import argparse
from collections import namedtuple
import contextlib
import unittest
import sys

import mock

from cloud_bdii.providers import openstack as os_provider
from cloud_bdii.tests import utils as test_utils


class OpenStackProviderOptionsTest(unittest.TestCase):
    def test_populate_parser(self):
        parser = argparse.ArgumentParser()
        provider = os_provider.OpenStackProvider
        provider.populate_parser(parser)

        opts = parser.parse_args(['--os-username', 'foo',
                                  '--os-password', 'bar',
                                  '--os-tenant-name', 'bazonk',
                                  '--os-auth-url', 'http://example.org:5000',
                                  '--os-cacert', 'foobar',
                                  '--insecure'])

        self.assertEqual(opts.os_username, 'foo')
        self.assertEqual(opts.os_password, 'bar')
        self.assertEqual(opts.os_tenant_name, 'bazonk')
        self.assertEqual(opts.os_auth_url, 'http://example.org:5000')
        self.assertEqual(opts.os_cacert, 'foobar')
        self.assertEqual(opts.insecure, True)

    def test_options(self):
        class Opts(object):
            os_username = os_password = os_tenant_name = os_tenant_id = 'foo'
            os_auth_url = 'http://foo.example.org'
            os_cacert = None
            insecure = False

        sys.modules['novaclient'] = mock.Mock()
        sys.modules['novaclient.client'] = mock.Mock()

        provider = os_provider.OpenStackProvider

        # Check that the required opts are there
        for opt in ('os_username', 'os_password', 'os_auth_url'):
            o = Opts()
            setattr(o, opt, None)
            self.assertRaises(SystemExit, provider, o)

        # Check that either tenant id or name are there
        o = Opts()
        setattr(o, 'os_tenant_name', None)
        setattr(o, 'os_tenant_id', None)
        self.assertRaises(SystemExit, provider, o)


class Fakes(object):
    def __init__(self):
        Flavor = namedtuple('Flavor',
                            ('id', 'name', 'ram', 'vcpus', 'is_public'))

        flavors = (
            {
                'id': 1,
                'name': 'foo',
                'ram': 10,
                'vcpus': 20,
                'is_public': True,
            },
            {
                'id': 2,
                'name': 'bar',
                'ram': 20,
                'vcpus': 30,
                'is_public': False,
            },
            {
                'id': 3,
                'name': 'baz',
                'ram': 2,
                'vcpus': 3,
                'is_public': True,
            },
        )

        self.flavors = [Flavor(**f) for f in flavors]

        Image = namedtuple('Image',
                           ('name', 'id', 'links', 'metadata'))

        images = (
            {
                'name': 'fooimage',
                'id': 'fooid',
                'metadata': {},
                'links': [{
                    'type': 'application/vnd.openstack.image',
                    'href': 'http://example.org/',
                }]
            },
            {
                'name': 'barimage',
                'id': 'barid',
                'metadata': {},
                'links': []
            },
        )
        self.images = [Image(**i) for i in images]

        catalog = (
            (
                'nova', 'compute', '1b7f14c87d8c42ad962f4d3a5fd13a77',
                'https://cloud.example.org:8774/v1.1/ce2d'
            ),
            (
                'ceilometer', 'metering', '5acd54c66f3641fd948fa363fa5c9d0a',
                'https://cloud.example.org:8777/'
            ),
            (
                'nova-volume', 'volume', '5afb318eedd44a71ab8362cc917f929b',
                'http://cloudvolume01.example.org:8776/v1/ce2d'
            ),
            (
                'ec2', 'ec2', '93ccd85773d24f238c6f2fab802cfd06',
                'https://cloud.example.org:8773/services/Admin'
            ),
            (
                'occi', 'occi', '03e087c8fb3b495c9a360bcba3abf914',
                'https://cloud.example.org:8787/'
            ),
            (
                'keystone', 'identity', '510c45b865ba4f40997b91a85552f3e2',
                'https://keystone.example.org:35357/v2.0'
            ),
            (
                'glance', 'image', '0ceb45ad3ee84f9ca5c1809b07715d40',
                'https://glance.example.org:9292/',
            ),
        )

        self.catalog = {
            'access': {
                'serviceCatalog': [],
            }
        }

        for name, type_, id_, url in catalog:
            service = {
                'endpoints': [{
                    'adminURL': url,
                    'publicURL': url,
                    'internalURL': url,
                    'id': id_,
                    'region': 'RegionOne'
                }],
                'endpoints_links': [],
                'name': name,
                'type': type_
            }
            self.catalog['access']['serviceCatalog'].append(service)


class OpenStackProviderTest(unittest.TestCase):
    def setUp(self):
        class FakeProvider(os_provider.OpenStackProvider):
            def __init__(self, opts):
                self.api = mock.Mock()
                self.static = mock.Mock()

        self.provider = FakeProvider(None)

    def __init__(self, *args):
        self.fakes = Fakes()
        super(OpenStackProviderTest, self).__init__(*args)

    def assert_resources(self, expected, observed, template=None):
        if template:
            fields = test_utils.get_variables_from_template(template)
        else:
            fields = []

        for k, v in observed.iteritems():
            self.assertDictEqual(expected[k], v)
            for f in fields:
                self.assertIn(f, v)

    def test_get_templates_with_defaults(self):
        expected_templates = {}
        for f in self.fakes.flavors:
            if not f.is_public:
                continue

            expected_templates[f.id] = {
                'template_memory': f.ram,
                'template_cpu': f.vcpus,
                'template_id': 'resource#%s' % f.name,
                'template_platform': 'amd64',
                'template_network': 'private'
            }

        with contextlib.nested(
            mock.patch.object(self.provider.static, 'get_template_defaults'),
            mock.patch.object(self.provider.api.flavors, 'list'),
        ) as (m_get_template_defaults, m_flavors_list):
            m_get_template_defaults.return_value = {}
            m_get_template_defaults.assert_called()
            m_flavors_list.return_value = self.fakes.flavors
            templates = self.provider.get_templates()

        self.assert_resources(expected_templates,
                              templates,
                              template="execution_environment.ldif")

    def test_get_templates_with_defaults_from_static(self):
        expected_templates = {}
        for f in self.fakes.flavors:
            if not f.is_public:
                continue

            expected_templates[f.id] = {
                'template_memory': f.ram,
                'template_cpu': f.vcpus,
                'template_id': 'resource#%s' % f.name,
                'template_platform': 'i686',
                'template_network': 'private'
            }

        with contextlib.nested(
            mock.patch.object(self.provider.static, 'get_template_defaults'),
            mock.patch.object(self.provider.api.flavors, 'list'),
        ) as (m_get_template_defaults, m_flavors_list):
            m_get_template_defaults.return_value = {
                'template_platform': 'i686'
            }
            m_get_template_defaults.assert_called()
            m_flavors_list.return_value = self.fakes.flavors
            templates = self.provider.get_templates()

        self.assert_resources(expected_templates,
                              templates,
                              template="execution_environment.ldif")

    def test_get_images(self):
        expected_images = {
            'barid': {
                'image_description': 'barimage',
                'image_name': 'barimage',
                'image_os_family': None,
                'image_os_name': None,
                'image_os_version': None,
                'image_platform': 'amd64',
                'image_version': None,
                'image_marketplace_id': None,
                'image_id': 'os#barid'
            },
            'fooid': {
                'image_description': 'fooimage',
                'image_name': 'fooimage',
                'image_os_family': None,
                'image_os_name': None,
                'image_os_version': None,
                'image_platform': 'amd64',
                'image_version': None,
                'image_marketplace_id': 'http://example.org/',
                'image_id': 'os#fooid'
            }
        }

        with contextlib.nested(
            mock.patch.object(self.provider.static, 'get_image_defaults'),
            mock.patch.object(self.provider.api.images, 'list'),
        ) as (m_get_image_defaults, m_images_list):
            m_get_image_defaults.return_value = {}
            m_get_image_defaults.assert_called()
            m_images_list.return_value = self.fakes.images

            images = self.provider.get_images()

        self.assert_resources(expected_images,
                              images,
                              template="application_environment.ldif")

    def test_get_endpoints_with_defaults_from_static(self):
        expected_endpoints = {
            'endpoints': {
                '03e087c8fb3b495c9a360bcba3abf914': {
                    'compute_api_type': 'OCCI',
                    'compute_api_version': '11.11',
                    'endpoint_url': 'https://cloud.example.org:8787/'},
                '1b7f14c87d8c42ad962f4d3a5fd13a77': {
                    'compute_api_type': 'OpenStack',
                    'compute_api_version': '99.99',
                    'endpoint_url': 'https://cloud.example.org:8774/v1.1/ce2d'}
            },
            'compute_middleware_developer': 'OpenStack',
            'compute_middleware': 'OpenStack Nova',
        }

        with mock.patch.object(
            self.provider.static, 'get_compute_endpoint_defaults'
        ) as m_get_endpoint_defaults:
            m_get_endpoint_defaults.return_value = {
                'endpoint_occi_api_version': '11.11',
                'endpoint_openstack_api_version': '99.99',
            }
            m_get_endpoint_defaults.assert_called()
            self.provider.api.client.service_catalog.catalog = \
                self.fakes.catalog
            endpoints = self.provider.get_compute_endpoints()

        self.assertDictEqual(expected_endpoints, endpoints)

    def test_get_endpoints_with_defaults(self):
        expected_endpoints = {
            'endpoints': {
                '03e087c8fb3b495c9a360bcba3abf914': {
                    'compute_api_type': 'OCCI',
                    'compute_api_version': '1.1',
                    'endpoint_url': 'https://cloud.example.org:8787/'},
                '1b7f14c87d8c42ad962f4d3a5fd13a77': {
                    'compute_api_type': 'OpenStack',
                    'compute_api_version': '2',
                    'endpoint_url': 'https://cloud.example.org:8774/v1.1/ce2d'}
            },
            'compute_middleware_developer': 'OpenStack',
            'compute_middleware': 'OpenStack Nova',
        }

        with mock.patch.object(
            self.provider.static, 'get_compute_endpoint_defaults'
        ) as m_get_endpoint_defaults:
            m_get_endpoint_defaults.return_value = {}
            m_get_endpoint_defaults.assert_called()
            self.provider.api.client.service_catalog.catalog = \
                self.fakes.catalog
            endpoints = self.provider.get_compute_endpoints()

        self.assertDictEqual(expected_endpoints, endpoints)
