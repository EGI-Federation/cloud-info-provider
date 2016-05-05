import argparse
import unittest
import uuid

import mock

from cloud_bdii import exceptions
from cloud_bdii.providers import opennebula
from cloud_bdii.tests import data

FAKES = data.ONE_FAKES


class OpenNebulaProviderOptionsTest(unittest.TestCase):
    def setUp(self):
        self.provider = opennebula.OpenNebulaProvider

    def test_populate_parser(self):
        parser = argparse.ArgumentParser()
        self.provider.populate_parser(parser)

        opts = parser.parse_args(['--on-auth', 'foo',
                                  '--on-rpcxml-endpoint',
                                  'bar'])

        self.assertEqual(opts.on_auth, 'foo')
        self.assertEqual(opts.on_rpcxml_endpoint, 'bar')

    def test_options(self):
        class Opts(object):
            on_auth = 'foo'
            on_rpcxml_endpoint = 'bar'

        # Check that the required opts are there
        for opt in ('on_auth', 'on_rpcxml_endpoint'):
            o = Opts()
            setattr(o, opt, None)
            self.assertRaises(exceptions.OpenNebulaProviderException,
                              self.provider, o)


class OpenNebulaProviderTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(OpenNebulaProviderTest, self).__init__(*args, **kwargs)
        self.expected_images = {
            0: {
                'image_description': 'OS Disk Image',
                'image_os_name': None,
                'image_name': 'Scientific-Linux-6.5-minimal@fedcloud-dukan',
                'image_marketplace_id': None,
                'image_id':
                'os_tpl#uuid_scientific_linux_6_5_minimal_fedcloud_dukan_85',
                'image_platform': 'amd64',
                'image_version': '20141029',
                'image_os_family': None,
                'image_os_version': None
            },
            1: {
                'image_description': None,
                'image_os_name': None,
                'image_name': 'Ubuntu-Server-14.04-LTS-ht-xxl@fedcloud-dukan',
                'image_marketplace_id': None,
                'image_id':
                'os_tpl#uuid_ubuntu_server_14_04_lts_ht_xxl_fedcloud_dukan_86',
                'image_platform': 'amd64',
                'image_version': '20141029',
                'image_os_family': None,
                'image_os_version': None
            }
        }
        self.provider_class = opennebula.OpenNebulaProvider

    def setUp(self):
        class FakeProvider(self.provider_class):
            def __init__(self, opts):
                self.on_auth = 'foo'
                self.on_rpcxml_endpoint = "http://foo.bar.com/"
                self.api = mock.Mock()
                self.static = mock.Mock()
                self.static.get_image_defaults.return_value = {}
                self.static.get_template_defaults.return_value = {}
                self.opts = opts

        class Opts(object):
            on_auth = 'foo'
            on_rpcxml_endpoint = 'bar'
            rocci_template_dir = 'foobar'
            vmcatcher_images = False

        self.provider = FakeProvider(Opts())

        class Templatepool:
            def info(self, a, b, c, d):
                return [True, FAKES.templatepool, 0]

        class Pool:
            def __init__(self, t):
                self.templatepool = t

        class Serverproxy:
            def __init__(self, o):
                self.one = o

        templatepool = Templatepool()
        pool = Pool(templatepool)
        self.mockedserverproxy = Serverproxy(pool)

    @mock.patch('xmlrpclib.ServerProxy')
    def test_get_images(self, serverproxy):
        self.maxDiff = None
        serverproxy.return_value = self.mockedserverproxy
        self.assertDictEqual(
            self.expected_images, self.provider.get_images())

    def test_templates_missing(self):
        fake_dir = uuid.uuid4().hex
        self.provider.opts.template_dir = fake_dir
        self.assertRaises(OSError, self.provider.get_templates)

    def test_load_templates(self):
        # TBD
        pass
