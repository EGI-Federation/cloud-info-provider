import argparse
import sys
import unittest

import mock

from cloud_info import exceptions
from cloud_info.providers import openstack as os_provider
from cloud_info.tests import data
from cloud_info.tests import utils as utils

FAKES = data.OS_FAKES


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
                                  '--insecure',
                                  '--legacy-occi-os'])

        self.assertEqual(opts.os_username, 'foo')
        self.assertEqual(opts.os_password, 'bar')
        self.assertEqual(opts.os_tenant_name, 'bazonk')
        self.assertEqual(opts.os_auth_url, 'http://example.org:5000')
        self.assertEqual(opts.os_cacert, 'foobar')
        self.assertEqual(opts.insecure, True)
        self.assertEqual(opts.legacy_occi_os, True)

    def test_options(self):
        class Opts(object):
            os_username = os_password = os_tenant_name = os_tenant_id = 'foo'
            os_auth_url = 'http://foo.example.org'
            os_cacert = None
            insecure = False
            legacy_occi_os = False

        sys.modules['novaclient'] = mock.Mock()
        sys.modules['novaclient.client'] = mock.Mock()

        provider = os_provider.OpenStackProvider

        # Check that the required opts are there
        for opt in ('os_username', 'os_password', 'os_auth_url'):
            o = Opts()
            setattr(o, opt, None)
            self.assertRaises(exceptions.OpenStackProviderException,
                              provider, o)

        # Check that either tenant id or name are there
        o = Opts()
        setattr(o, 'os_tenant_name', None)
        setattr(o, 'os_tenant_id', None)
        self.assertRaises(exceptions.OpenStackProviderException, provider, o)


class OpenStackProviderTest(unittest.TestCase):
    def setUp(self):
        class FakeProvider(os_provider.OpenStackProvider):
            def __init__(self, opts):
                self.api = mock.Mock()
                self.api.client.auth_url = 'http://foo.example.org:1234/v2'
                self.static = mock.Mock()
                self.legacy_occi_os = False

        self.provider = FakeProvider(None)

    def assert_resources(self, expected, observed, template=None,
                         ignored_fields=[]):
        if template:
            fields = utils.get_variables_from_template(template,
                                                       ignored_fields)
        else:
            fields = []
        for k, v in observed.items():
            self.assertDictEqual(expected[k], v)
            for f in fields:
                self.assertIn(f, v)

    def test_get_legacy_templates_with_defaults(self):
        expected_templates = {}
        for f in FAKES.flavors:
            if not f.is_public:
                continue

            name = f.name.strip().replace(' ', '_').replace('.', '-').lower()
            expected_templates[f.id] = {
                'template_memory': f.ram,
                'template_cpu': f.vcpus,
                'template_id': 'resource_tpl#%s' % name,
                'template_platform': 'amd64',
                'template_network': 'private'
            }

        self.provider.legacy_occi_os = True
        with utils.nested(
            mock.patch.object(self.provider.static, 'get_template_defaults'),
            mock.patch.object(self.provider.api.flavors, 'list'),
        ) as (m_get_template_defaults, m_flavors_list):
            m_get_template_defaults.return_value = {}
            m_flavors_list.return_value = FAKES.flavors
            templates = self.provider.get_templates()
            assert m_get_template_defaults.called

        self.assert_resources(expected_templates,
                              templates,
                              template="execution_environment.ldif",
                              ignored_fields=["compute_service_name"])

    def test_get_legacy_templates_with_defaults_from_static(self):
        expected_templates = {}
        for f in FAKES.flavors:
            if not f.is_public:
                continue

            name = f.name.strip().replace(' ', '_').replace('.', '-').lower()
            expected_templates[f.id] = {
                'template_memory': f.ram,
                'template_cpu': f.vcpus,
                'template_id': 'resource_tpl#%s' % name,
                'template_platform': 'i686',
                'template_network': 'private'
            }

        self.provider.legacy_occi_os = True
        with utils.nested(
            mock.patch.object(self.provider.static, 'get_template_defaults'),
            mock.patch.object(self.provider.api.flavors, 'list'),
        ) as (m_get_template_defaults, m_flavors_list):
            m_get_template_defaults.return_value = {
                'template_platform': 'i686'
            }
            m_flavors_list.return_value = FAKES.flavors
            templates = self.provider.get_templates()
            assert m_get_template_defaults.called

        self.assert_resources(expected_templates,
                              templates,
                              template="execution_environment.ldif",
                              ignored_fields=["compute_service_name"])

    def test_get_templates_with_defaults(self):
        expected_templates = {}
        for f in FAKES.flavors:
            if not f.is_public:
                continue

            expected_templates[f.id] = {
                'template_memory': f.ram,
                'template_cpu': f.vcpus,
                'template_id': 'resource_tpl#%s' % f.id,
                'template_platform': 'amd64',
                'template_network': 'private'
            }

        with utils.nested(
            mock.patch.object(self.provider.static, 'get_template_defaults'),
            mock.patch.object(self.provider.api.flavors, 'list'),
        ) as (m_get_template_defaults, m_flavors_list):
            m_get_template_defaults.return_value = {}
            m_flavors_list.return_value = FAKES.flavors
            templates = self.provider.get_templates()
            assert m_get_template_defaults.called

        self.assert_resources(expected_templates,
                              templates,
                              template="execution_environment.ldif",
                              ignored_fields=["compute_service_name"])

    def test_get_templates_with_defaults_from_static(self):
        expected_templates = {}
        for f in FAKES.flavors:
            if not f.is_public:
                continue

            expected_templates[f.id] = {
                'template_memory': f.ram,
                'template_cpu': f.vcpus,
                'template_id': 'resource_tpl#%s' % f.id,
                'template_platform': 'i686',
                'template_network': 'private'
            }

        with utils.nested(
            mock.patch.object(self.provider.static, 'get_template_defaults'),
            mock.patch.object(self.provider.api.flavors, 'list'),
        ) as (m_get_template_defaults, m_flavors_list):
            m_get_template_defaults.return_value = {
                'template_platform': 'i686'
            }
            m_flavors_list.return_value = FAKES.flavors
            templates = self.provider.get_templates()
            assert m_get_template_defaults.called

        self.assert_resources(expected_templates,
                              templates,
                              template="execution_environment.ldif",
                              ignored_fields=["compute_service_name"])

    def test_get_images(self):
        # XXX move this to a custom class?
        # XXX add docker information
        expected_images = {
            'bar id': {
                'image_description': None,
                'image_name': 'barimage',
                'image_os_family': None,
                'image_os_name': None,
                'image_os_version': None,
                'image_platform': 'amd64',
                'image_version': None,
                'image_marketplace_id': None,
                'image_id': 'os_tpl#bar_id'
            },
            'foo.id': {
                'image_description': None,
                'image_name': 'fooimage',
                'image_os_family': None,
                'image_os_name': None,
                'image_os_version': None,
                'image_platform': 'amd64',
                'image_version': None,
                'image_marketplace_id': 'http://example.org/',
                'image_id': 'os_tpl#foo-id'
            },
            'baz id': {
                'image_description': None,
                'image_name': 'bazimage',
                'image_os_family': None,
                'image_os_name': None,
                'image_os_version': None,
                'image_platform': 'amd64',
                'image_version': None,
                'image_marketplace_id': None,
                'image_id': 'os_tpl#baz_id',
                'docker_id': 'sha1:xxxxxxxxxxxxxxxxxxxxxxxxxx',
                'docker_tag': 'latest',
                'docker_name': 'test/image'
            }
        }

        with utils.nested(
            mock.patch.object(self.provider.static, 'get_image_defaults'),
            mock.patch.object(self.provider.api.images, 'list'),
        ) as (m_get_image_defaults, m_images_list):
            m_get_image_defaults.return_value = {}
            m_images_list.return_value = FAKES.images

            images = self.provider.get_images()
            assert m_get_image_defaults.called

        self.assert_resources(expected_images,
                              images,
                              template="application_environment.ldif",
                              ignored_fields=["compute_service_name"])

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
            'compute_service_name': 'http://foo.example.org:1234/v2',
        }

        with mock.patch.object(
            self.provider.static, 'get_compute_endpoint_defaults'
        ) as m_get_endpoint_defaults:
            m_get_endpoint_defaults.return_value = {
                'endpoint_occi_api_version': '11.11',
                'endpoint_openstack_api_version': '99.99',
            }
            self.provider.api.client.service_catalog.catalog = FAKES.catalog
            endpoints = self.provider.get_compute_endpoints()
            assert m_get_endpoint_defaults.called

        for k, v in expected_endpoints['endpoints'].items():
            self.assertDictContainsSubset(v, endpoints['endpoints'].get(k, {}))

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
            'compute_service_name': 'http://foo.example.org:1234/v2',
        }

        with mock.patch.object(
            self.provider.static, 'get_compute_endpoint_defaults'
        ) as m_get_endpoint_defaults:
            m_get_endpoint_defaults.return_value = {}
            self.provider.api.client.service_catalog.catalog = FAKES.catalog
            endpoints = self.provider.get_compute_endpoints()
            assert m_get_endpoint_defaults.called

        self.assertDictEqual(expected_endpoints, endpoints)

    def test_occify_terms(self):
        self.assertEqual('m1-tiny', self.provider.occify('m1.tiny'))
        self.assertEqual('m1_tiny', self.provider.occify('m1 tiny'))
        self.assertEqual('m1-tiny_s', self.provider.occify('m1.tiny s'))
