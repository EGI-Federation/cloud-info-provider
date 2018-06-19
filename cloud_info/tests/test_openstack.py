import argparse
import unittest

import mock

from cloud_info.providers import openstack as os_provider
from cloud_info.tests import base
from cloud_info.tests import data
from cloud_info.tests import utils as utils

FAKES = data.OS_FAKES


class OpenStackProviderOptionsTest(base.TestCase):
    def test_populate_parser(self):
        parser = argparse.ArgumentParser()
        provider = os_provider.OpenStackProvider
        provider.populate_parser(parser)

        opts = parser.parse_args(['--os-username', 'foo',
                                  '--os-password', 'bar',
                                  '--os-auth-url', 'http://example.org:5000',
                                  '--os-cacert', 'foobar',
                                  '--insecure',
                                  '--legacy-occi-os'])

        self.assertEqual(opts.os_username, 'foo')
        self.assertEqual(opts.os_password, 'bar')
        self.assertEqual(opts.os_auth_url, 'http://example.org:5000')
        self.assertEqual(opts.os_cacert, 'foobar')
        self.assertEqual(opts.insecure, True)
        self.assertEqual(opts.legacy_occi_os, True)


class OpenStackProviderTest(base.TestCase):
    def setUp(self):
        super(OpenStackProviderTest, self).setUp()

        class FakeProvider(os_provider.OpenStackProvider):
            def __init__(self, opts):
                self.nova = mock.Mock()
                self.glance = mock.Mock()
                self.glance.http_client.get_endpoint.return_value = (
                    "http://glance.example.org:9292/v2"
                )
                self.session = None
                self.auth_plugin = mock.MagicMock()
                self.auth_plugin.auth_url = 'http://foo.example.org:1234/v2'
                self.static = mock.Mock()
                self.legacy_occi_os = False
                self.keystone_cert_issuer = "foo"
                self.keystone_trusted_cas = []
                self.insecure = False

            def _get_endpoint_versions(*args, **kwargs):
                return {
                    'compute_middleware_version': None,
                    'compute_api_version': None,
                }

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
        url = 'http://schemas.openstack.org/template/resource'
        for f in FAKES.flavors:
            name = f.name.strip().replace(' ', '_').replace('.', '-').lower()
            expected_templates[f.id] = {
                'template_memory': f.ram,
                'template_cpu': f.vcpus,
                'template_id': '%s#%s' % (url, name),
                'template_platform': 'amd64',
                'template_network': 'private',
                'template_disk': f.disk,
            }

        self.provider.legacy_occi_os = True
        with utils.nested(
                mock.patch.object(self.provider.static,
                                  'get_template_defaults'),
                mock.patch.object(self.provider.nova.flavors, 'list'),
        ) as (m_get_template_defaults, m_flavors_list):
            m_get_template_defaults.return_value = {}
            m_flavors_list.return_value = FAKES.flavors
            templates = self.provider.get_templates()
            assert m_get_template_defaults.called

        self.assert_resources(expected_templates,
                              templates,
                              template="compute.ldif",
                              ignored_fields=[
                                  "compute_api_type",
                                  "compute_api_version",
                                  "compute_api_endpoint_technology",
                                  "compute_capabilities",
                                  "compute_endpoint_url",
                                  "compute_hypervisor",
                                  "compute_hypervisor_version",
                                  "compute_middleware",
                                  "compute_middleware_developer",
                                  "compute_middleware_version",
                                  "compute_production_level",
                                  "compute_api_authn_method",
                                  "compute_service_name",
                                  "compute_service_production_level",
                                  "compute_total_cores",
                                  "compute_total_ram",
                                  "image_id",
                                  "image_name",
                                  "image_version",
                                  "image_description",
                                  "image_marketplace_id"
                              ])

    def test_get_legacy_templates_with_defaults_from_static(self):
        expected_templates = {}
        url = 'http://schemas.openstack.org/template/resource'
        for f in FAKES.flavors:
            name = f.name.strip().replace(' ', '_').replace('.', '-').lower()
            expected_templates[f.id] = {
                'template_memory': f.ram,
                'template_cpu': f.vcpus,
                'template_id': '%s#%s' % (url, name),
                'template_platform': 'i686',
                'template_network': 'private',
                'template_disk': f.disk,
            }

        self.provider.legacy_occi_os = True
        with utils.nested(
                mock.patch.object(self.provider.static,
                                  'get_template_defaults'),
                mock.patch.object(self.provider.nova.flavors, 'list'),
        ) as (m_get_template_defaults, m_flavors_list):
            m_get_template_defaults.return_value = {
                'template_platform': 'i686'
            }
            m_flavors_list.return_value = FAKES.flavors
            templates = self.provider.get_templates()
            assert m_get_template_defaults.called

        self.assert_resources(expected_templates,
                              templates,
                              template="compute.ldif",
                              ignored_fields=[
                                  "compute_api_type",
                                  "compute_api_version",
                                  "compute_api_endpoint_technology",
                                  "compute_capabilities",
                                  "compute_endpoint_url",
                                  "compute_hypervisor",
                                  "compute_hypervisor_version",
                                  "compute_middleware",
                                  "compute_middleware_developer",
                                  "compute_middleware_version",
                                  "compute_production_level",
                                  "compute_api_authn_method",
                                  "compute_service_name",
                                  "compute_service_production_level",
                                  "compute_total_cores",
                                  "compute_total_ram",
                                  "image_id",
                                  "image_name",
                                  "image_version",
                                  "image_description",
                                  "image_marketplace_id"
                              ])

    def test_get_templates_with_defaults(self):
        expected_templates = {}
        url = 'http://schemas.openstack.org/template/resource'
        for f in FAKES.flavors:
            expected_templates[f.id] = {
                'template_memory': f.ram,
                'template_cpu': f.vcpus,
                'template_id': '%s#%s' % (url, f.id),
                'template_platform': 'amd64',
                'template_network': 'private',
                'template_disk': f.disk,
            }

        with utils.nested(
                mock.patch.object(self.provider.static,
                                  'get_template_defaults'),
                mock.patch.object(self.provider.nova.flavors, 'list'),
        ) as (m_get_template_defaults, m_flavors_list):
            m_get_template_defaults.return_value = {}
            m_flavors_list.return_value = FAKES.flavors
            templates = self.provider.get_templates()
            assert m_get_template_defaults.called

        self.assert_resources(expected_templates,
                              templates,
                              template="compute.ldif",
                              ignored_fields=[
                                  "compute_api_type",
                                  "compute_api_version",
                                  "compute_api_endpoint_technology",
                                  "compute_capabilities",
                                  "compute_endpoint_url",
                                  "compute_hypervisor",
                                  "compute_hypervisor_version",
                                  "compute_middleware",
                                  "compute_middleware_developer",
                                  "compute_middleware_version",
                                  "compute_production_level",
                                  "compute_api_authn_method",
                                  "compute_service_name",
                                  "compute_service_production_level",
                                  "compute_total_cores",
                                  "compute_total_ram",
                                  "image_id",
                                  "image_name",
                                  "image_version",
                                  "image_description",
                                  "image_marketplace_id"
                              ])

    def test_get_templates_with_defaults_from_static(self):
        expected_templates = {}
        url = 'http://schemas.openstack.org/template/resource'
        for f in FAKES.flavors:
            expected_templates[f.id] = {
                'template_memory': f.ram,
                'template_cpu': f.vcpus,
                'template_id': '%s#%s' % (url, f.id),
                'template_platform': 'i686',
                'template_network': 'private',
                'template_disk': f.disk,
            }

        with utils.nested(
                mock.patch.object(self.provider.static,
                                  'get_template_defaults'),
                mock.patch.object(self.provider.nova.flavors, 'list'),
        ) as (m_get_template_defaults, m_flavors_list):
            m_get_template_defaults.return_value = {
                'template_platform': 'i686'
            }
            m_flavors_list.return_value = FAKES.flavors
            templates = self.provider.get_templates()
            assert m_get_template_defaults.called

        self.assert_resources(expected_templates,
                              templates,
                              template="compute.ldif",
                              ignored_fields=[
                                  "compute_api_type",
                                  "compute_api_version",
                                  "compute_api_endpoint_technology",
                                  "compute_capabilities",
                                  "compute_endpoint_url",
                                  "compute_hypervisor",
                                  "compute_hypervisor_version",
                                  "compute_middleware",
                                  "compute_middleware_developer",
                                  "compute_middleware_version",
                                  "compute_production_level",
                                  "compute_api_authn_method",
                                  "compute_service_name",
                                  "compute_service_production_level",
                                  "compute_total_cores",
                                  "compute_total_ram",
                                  "image_id",
                                  "image_name",
                                  "image_version",
                                  "image_description",
                                  "image_marketplace_id"
                              ])

    def test_get_all_templates(self):
        """Tests that all templates/flavors are returned"""
        expected_templates = {}
        url = 'http://schemas.openstack.org/template/resource'
        for f in FAKES.flavors:
            expected_templates[f.id] = {
                'template_memory': f.ram,
                'template_cpu': f.vcpus,
                'template_id': '%s#%s' % (url, f.id),
                'template_platform': 'i686',
                'template_network': 'private',
                'template_disk': f.disk,
            }

        with utils.nested(
                mock.patch.object(self.provider.static,
                                  'get_template_defaults'),
                mock.patch.object(self.provider.nova.flavors, 'list'),
        ) as (m_get_template_defaults, m_flavors_list):
            m_get_template_defaults.return_value = {
                'template_platform': 'i686'
            }
            m_flavors_list.return_value = FAKES.flavors
            filter = 'all'
            templates = self.provider.get_templates(filter)
            assert m_get_template_defaults.called

        # Extract required fields from compute.ldif template excluding fields
        # extracted that are not related to the flavors
        self.assert_resources(expected_templates,
                              templates,
                              template="compute.ldif",
                              ignored_fields=[
                                  "compute_service_name",
                                  "compute_hypervisor",
                                  "compute_api_authn_method",
                                  "compute_total_ram",
                                  "image_marketplace_id",
                                  "compute_middleware_developer",
                                  "compute_production_level",
                                  "compute_production_level",
                                  "compute_api_type",
                                  "compute_api_endpoint_technology",
                                  "compute_api_version",
                                  "compute_endpoint_url",
                                  "compute_service_production_level",
                                  "compute_capabilities",
                                  "compute_total_cores",
                                  "compute_middleware",
                                  "compute_hypervisor_version",
                                  "compute_middleware_version",
                                  "image_description",
                                  "image_id",
                                  "image_name",
                                  "image_version"
                              ])

    def test_get_public_templates(self):
        """Tests that only public templates/flavors are returned"""
        expected_templates = {}
        url = 'http://schemas.openstack.org/template/resource'
        for f in FAKES.flavors:
            if not f.is_public:
                continue

            expected_templates[f.id] = {
                'template_memory': f.ram,
                'template_cpu': f.vcpus,
                'template_id': '%s#%s' % (url, f.id),
                'template_platform': 'i686',
                'template_network': 'private',
                'template_disk': f.disk,
            }

        with utils.nested(
                mock.patch.object(self.provider.static,
                                  'get_template_defaults'),
                mock.patch.object(self.provider.nova.flavors, 'list'),
        ) as (m_get_template_defaults, m_flavors_list):
            m_get_template_defaults.return_value = {
                'template_platform': 'i686'
            }
            m_flavors_list.return_value = FAKES.flavors
            filter = 'public'
            templates = self.provider.get_templates(filter)
            assert m_get_template_defaults.called

        # Extract required fields from compute.ldif template excluding fields
        # extracted that are not related to the flavors
        self.assert_resources(expected_templates,
                              templates,
                              template="compute.ldif",
                              ignored_fields=[
                                  "compute_service_name",
                                  "compute_hypervisor",
                                  "compute_api_authn_method",
                                  "compute_total_ram",
                                  "image_marketplace_id",
                                  "compute_middleware_developer",
                                  "compute_production_level",
                                  "compute_production_level",
                                  "compute_api_type",
                                  "compute_api_endpoint_technology",
                                  "compute_api_version",
                                  "compute_endpoint_url",
                                  "compute_service_production_level",
                                  "compute_capabilities",
                                  "compute_total_cores",
                                  "compute_middleware",
                                  "compute_hypervisor_version",
                                  "compute_middleware_version",
                                  "image_description",
                                  "image_id",
                                  "image_name",
                                  "image_version"
                              ])

    def test_get_private_templates(self):
        """Tests that only private templates/flavors are returned"""
        expected_templates = {}
        url = 'http://schemas.openstack.org/template/resource'
        for f in FAKES.flavors:
            if f.is_public:
                continue

            expected_templates[f.id] = {
                'template_memory': f.ram,
                'template_cpu': f.vcpus,
                'template_id': '%s#%s' % (url, f.id),
                'template_platform': 'i686',
                'template_network': 'private',
                'template_disk': f.disk,
            }

        with utils.nested(
                mock.patch.object(self.provider.static,
                                  'get_template_defaults'),
                mock.patch.object(self.provider.nova.flavors, 'list'),
        ) as (m_get_template_defaults, m_flavors_list):
            m_get_template_defaults.return_value = {
                'template_platform': 'i686'
            }
            m_flavors_list.return_value = FAKES.flavors
            filter = 'private'
            templates = self.provider.get_templates(filter)
            assert m_get_template_defaults.called

        # Extract required fields from compute.ldif template excluding fields
        # extracted that are not related to the flavors
        self.assert_resources(expected_templates,
                              templates,
                              template="compute.ldif",
                              ignored_fields=[
                                  "compute_service_name",
                                  "compute_hypervisor",
                                  "compute_api_authn_method",
                                  "compute_total_ram",
                                  "image_marketplace_id",
                                  "compute_middleware_developer",
                                  "compute_production_level",
                                  "compute_production_level",
                                  "compute_api_type",
                                  "compute_api_endpoint_technology",
                                  "compute_api_version",
                                  "compute_endpoint_url",
                                  "compute_service_production_level",
                                  "compute_capabilities",
                                  "compute_total_cores",
                                  "compute_middleware",
                                  "compute_hypervisor_version",
                                  "compute_middleware_version",
                                  "image_description",
                                  "image_id",
                                  "image_name",
                                  "image_version"
                              ])

    @unittest.expectedFailure
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
                'image_id': 'http://schemas.openstack.org/template/os#bar_id'
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
                'image_id': 'http://schemas.openstack.org/template/os#foo-id'
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
                'image_id': 'http://schemas.openstack.org/template/os#baz_id',
                'docker_id': 'sha1:xxxxxxxxxxxxxxxxxxxxxxxxxx',
                'docker_tag': 'latest',
                'docker_name': 'test/image'
            }
        }

        with utils.nested(
                mock.patch.object(self.provider.static, 'get_image_defaults'),
                mock.patch.object(self.provider.glance.images, 'list'),
        ) as (m_get_image_defaults, m_images_list):
            m_get_image_defaults.return_value = {}
            m_images_list.return_value = FAKES.images

            images = self.provider.get_images()
            assert m_get_image_defaults.called

        self.assert_resources(expected_images,
                              images,
                              template="compute.ldif",
                              ignored_fields=["compute_service_name"])

    @unittest.expectedFailure
    def test_get_endpoints_with_defaults_from_static(self):
        expected_endpoints = {
            'endpoints': {
                '03e087c8fb3b495c9a360bcba3abf914': {
                    'compute_api_type': 'OCCI',
                    'compute_api_version': '11.11',
                    'compute_endpoint_url': 'https://cloud.example.org:8787/'},
                '1b7f14c87d8c42ad962f4d3a5fd13a77': {
                    'compute_api_type': 'OpenStack',
                    'compute_api_version': '99.99',
                    'compute_endpoint_url':
                        'https://cloud.example.org:8774/v1.1/ce2d'}
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
            r = mock.Mock()
            r.service_catalog = FAKES.catalog
            self.provider.auth_plugin.get_access.return_value = r
            endpoints = self.provider.get_compute_endpoints()
            assert m_get_endpoint_defaults.called

        for k, v in expected_endpoints['endpoints'].items():
            self.assertDictContainsSubset(v, endpoints['endpoints'].get(k, {}))

    @unittest.expectedFailure
    def test_get_endpoints_with_defaults(self):
        expected_endpoints = {
            'endpoints': {
                '03e087c8fb3b495c9a360bcba3abf914': {
                    'compute_api_type': 'OCCI',
                    'compute_api_version': '1.1',
                    'compute_endpoint_url': 'https://cloud.example.org:8787/'},
                '1b7f14c87d8c42ad962f4d3a5fd13a77': {
                    'compute_api_type': 'OpenStack',
                    'compute_api_version': '2',
                    'compute_endpoint_url':
                        'https://cloud.example.org:8774/v1.1/ce2d'}
            },
            'compute_middleware_developer': 'OpenStack',
            'compute_middleware': 'OpenStack Nova',
            'compute_service_name': 'http://foo.example.org:1234/v2',
        }

        with mock.patch.object(
                self.provider.static, 'get_compute_endpoint_defaults'
        ) as m_get_endpoint_defaults:
            m_get_endpoint_defaults.return_value = {}
            r = mock.Mock()
            r.service_catalog = FAKES.catalog
            self.provider.auth_plugin.get_access.return_value = r
            endpoints = self.provider.get_compute_endpoints()
            assert m_get_endpoint_defaults.called

        self.assertDictEqual(expected_endpoints, endpoints)

    def test_occify_terms(self):
        self.assertEqual('m1-tiny', self.provider.occify('m1.tiny'))
        self.assertEqual('m1_tiny', self.provider.occify('m1 tiny'))
        self.assertEqual('m1-tiny_s', self.provider.occify('m1.tiny s'))
