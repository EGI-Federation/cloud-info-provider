import argparse
import mock
import xml.etree.ElementTree

from cloud_info_provider import exceptions
from cloud_info_provider.providers import opennebula
from cloud_info_provider.tests import base
from cloud_info_provider.tests import data

FAKES = data.ONE_FAKES


class OpenNebulaBaseProviderOptionsTest(base.TestCase):
    def setUp(self):
        super(OpenNebulaBaseProviderOptionsTest, self).setUp()

        self.provider = opennebula.OpenNebulaBaseProvider

    def test_populate_parser(self):
        parser = argparse.ArgumentParser()
        self.provider.populate_parser(parser)

        opts = parser.parse_args(['--on-auth', 'foo',
                                  '--on-rpcxml-endpoint', 'bar',
                                  '--all-images'])

        self.assertEqual(opts.on_auth, 'foo')
        self.assertEqual(opts.on_rpcxml_endpoint, 'bar')
        self.assertTrue(opts.all_images)

    def test_options(self):
        class Opts(object):
            on_auth = 'foo'
            on_rpcxml_endpoint = 'bar'
            all_images = True

        # Check that the required opts are there
        for opt in ('on_auth', 'on_rpcxml_endpoint'):
            o = Opts()
            setattr(o, opt, None)
            self.assertRaises(exceptions.OpenNebulaProviderException,
                              self.provider, o)


class OpenNebulaProviderOptionsTest(OpenNebulaBaseProviderOptionsTest):
    def setUp(self):
        super(OpenNebulaProviderOptionsTest, self).setUp()

        self.provider = opennebula.OpenNebulaProvider


class OpenNebulaROCCIProviderOptionsTest(OpenNebulaBaseProviderOptionsTest):
    def setUp(self):
        super(OpenNebulaROCCIProviderOptionsTest, self).setUp()
        self.provider = opennebula.OpenNebulaROCCIProvider

    def test_populate_parser(self):
        parser = argparse.ArgumentParser()
        self.provider.populate_parser(parser)

        opts = parser.parse_args(['--on-auth', 'foo',
                                  '--on-rpcxml-endpoint', 'bar',
                                  '--rocci-template-dir', 'test',
                                  '--all-images'])

        self.assertEqual(opts.on_auth, 'foo')
        self.assertEqual(opts.on_rpcxml_endpoint, 'bar')
        self.assertEqual(opts.rocci_template_dir, 'test')
        self.assertTrue(opts.all_images)

    def test_options(self):
        class Opts(object):
            on_auth = 'foo'
            on_rpcxml_endpoint = 'bar'
            rocci_template_dir = 'test'
            rocci_remote_templates = False
            all_images = False

        # Check that the required opts are there
        for opt in ('on_auth', 'on_rpcxml_endpoint', 'rocci_template_dir'):
            o = Opts()
            setattr(o, opt, None)
            self.assertRaises(exceptions.OpenNebulaProviderException,
                              self.provider, o)


class IndigoONProviderOptionsTest(OpenNebulaBaseProviderOptionsTest):
    def setUp(self):
        super(IndigoONProviderOptionsTest, self).setUp()
        self.provider = opennebula.IndigoONProvider


class OpenNebulaBaseProviderTest(base.TestCase):
    def __init__(self, *args, **kwargs):
        super(OpenNebulaBaseProviderTest, self).__init__(*args, **kwargs)
        self.provider_class = opennebula.OpenNebulaBaseProvider
        self.maxDiff = None
        self.expected_images = FAKES.opennebula_base_provider_expected_images

    def setUp(self):
        super(OpenNebulaBaseProviderTest, self).setUp()

        class FakeProvider(self.provider_class):
            def __init__(self, opts):
                self.opts = opts
                self.on_auth = opts.on_auth
                self.on_rpcxml_endpoint = opts.on_rpcxml_endpoint
                self.all_images = opts.all_images

                self.static = mock.Mock()
                self.static.get_image_defaults.return_value = {}

                self.xml_parser = xml.etree.ElementTree
                self.server_proxy = mock.Mock()
                self.server_proxy.one.templatepool.info.return_value = (
                    'OK', FAKES.templatepool)

        class Opts(object):
            on_auth = 'oneadmin:opennebula'
            on_rpcxml_endpoint = 'http://localhost:2633/RPC2'
            all_images = True

        self.provider = FakeProvider(Opts())

    def test_get_images(self):
        self.assertDictEqual(
            self.expected_images, self.provider.get_images())

    def test_get_marketplace_images(self):
        self.provider.all_images = False
        marketplace_images = {k: v for k, v in self.expected_images.items()
                              if v.get('image_marketplace_id')}
        self.assertItemsEqual(marketplace_images.keys(),
                              self.provider.get_images().keys())

    def test_get_templates(self):
        self.assertDictEqual({}, self.provider.get_templates())


class OpenNebulaProviderTest(OpenNebulaBaseProviderTest):
    def __init__(self, *args, **kwargs):
        super(OpenNebulaProviderTest, self).__init__(*args, **kwargs)
        self.provider_class = opennebula.OpenNebulaProvider


class OpenNebulaROCCIProviderTest(OpenNebulaBaseProviderTest):
    def __init__(self, *args, **kwargs):
        super(OpenNebulaROCCIProviderTest, self).__init__(*args, **kwargs)
        self.provider_class = opennebula.OpenNebulaROCCIProvider
        self.expected_images = FAKES.opennebula_rocci_provider_expected_images
        self.expected_templates = \
            FAKES.opennebula_rocci_provider_expected_templates
        self.expected_templates_remote = \
            FAKES.opennebula_rocci_provider_expected_templates_remote

    def setUp(self):
        super(OpenNebulaROCCIProviderTest, self).setUp()

        class FakeProvider(self.provider_class):
            def __init__(self, opts):
                self.opts = opts
                self.on_auth = opts.on_auth
                self.on_rpcxml_endpoint = opts.on_rpcxml_endpoint
                self.rocci_template_dir = opts.rocci_template_dir
                self.rocci_remote_templates = opts.rocci_remote_templates
                self.all_images = opts.all_images

                self.xml_parser = xml.etree.ElementTree
                self.static = mock.Mock()
                self.static.get_image_defaults.return_value = {}
                self.static.get_template_defaults.return_value = {}
                self.server_proxy = mock.Mock()
                self.server_proxy.one.templatepool.info.return_value = (
                    'OK', FAKES.templatepool)
                self.server_proxy.one.imagepool.info.return_value = (
                    'OK', FAKES.imagepool)
                self.server_proxy.one.documentpool.info.return_value = (
                    'OK', FAKES.documentpool)

        class Opts(object):
            on_auth = 'foo'
            on_rpcxml_endpoint = 'bar'
            rocci_template_dir = FAKES.rocci_dir
            rocci_remote_templates = False
            all_images = True

        class OptsRemote(object):
            on_auth = 'foo'
            on_rpcxml_endpoint = 'bar'
            rocci_template_dir = ''
            rocci_remote_templates = True
            all_images = True

        self.provider = FakeProvider(Opts())
        self.provider_remote = FakeProvider(OptsRemote())

    def test_get_templates(self):
        self.assertDictEqual(
            self.expected_templates,
            self.provider.get_templates())

    def test_get_templates_remote(self):
        self.assertDictEqual(
            self.expected_templates_remote,
            self.provider_remote.get_templates())


class IndigoONProviderTest(OpenNebulaBaseProviderTest):
    def __init__(self, *args, **kwargs):
        super(IndigoONProviderTest, self).__init__(*args, **kwargs)
        self.provider_class = opennebula.IndigoONProvider
        self.expected_images = FAKES.indigo_on_provider_expected_images
        self.expected_templates = FAKES.indigo_on_provider_expected_templates

    def setUp(self):
        super(IndigoONProviderTest, self).setUp()

        class FakeProvider(self.provider_class):
            def __init__(self, opts):
                self.opts = opts
                self.on_auth = opts.on_auth
                self.on_rpcxml_endpoint = opts.on_rpcxml_endpoint
                self.all_images = opts.all_images

                self.xml_parser = xml.etree.ElementTree
                self.static = mock.Mock()
                self.static.get_image_defaults.return_value = {}
                self.static.get_template_defaults.return_value = {}
                self.server_proxy = mock.Mock()
                self.server_proxy.one.templatepool.info.return_value = (
                    'OK', FAKES.templatepool)
                self.server_proxy.one.imagepool.info.return_value = (
                    'OK', FAKES.imagepool)

        class Opts(object):
            on_auth = 'foo'
            on_rpcxml_endpoint = 'bar'
            all_images = True

        self.provider = FakeProvider(Opts())

    def test_get_templates(self):
        self.assertDictEqual(
            self.expected_templates, self.provider.get_templates())
