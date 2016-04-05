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
                                  '--on-rpcxml-endpoint', 'bar',
                                  '--vmcatcher-images'])

        self.assertEqual(opts.on_auth, 'foo')
        self.assertEqual(opts.on_rpcxml_endpoint, 'bar')
        self.assertTrue(opts.vmcatcher_images)

    def test_options(self):
        class Opts(object):
            on_auth = 'foo'
            on_rpcxml_endpoint = 'bar'
            vmcatcher_images = False

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
            '80': {
                'image_marketplace_id': (
                    'https://appdb.egi.eu/store/vm/image/'
                    'c0482bc2-bf41-5d49-a85f-a750174a186b:642/'
                ),
                'image_version': '3.3.0-1',
                'image_platform': 'amd64',
                'image_os_version': None,
                'image_name': 'CERNVM-3.3.0-40GB@fedcloud-dukan',
                'image_id': 'os_tpl#uuid_cernvm_3_3_0_40gb_fedcloud_dukan_80',
                'image_description': (
                    'This version of CERNVM has been modified by EGI with '
                    'the followign changes - default OS extended to 40GB '
                    'of disk - updated OpenNebula Cloud-Init driver to '
                    'latest version 0.7.5 - enabled all Cloud-Init data '
                    'sources'
                ),
                'image_os_name': None,
                'image_os_family': None
            },
            '86': {
                'image_marketplace_id': None,
                'image_version': None,
                'image_platform': 'amd64',
                'image_os_version': None,
                'image_name': 'Ubuntu-Server-14.04-LTS-ht-xxl@fedcloud-dukan',
                'image_id': 'os_tpl#uuid_ubuntu_server_14_04_lts_ht_xxl_fedcloud_dukan_86',
                'image_description': None,
                'image_os_name': None,
                'image_os_family': None},
        }
        self.provider_class = opennebula.OpenNebulaProvider

    def setUp(self):
        class FakeProvider(self.provider_class):
            def __init__(self, opts):
                self.on_auth = None
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
    
    @mock.patch('xmlrpccall')
    def test_get_images(self, mock_open):
        resp = mock.Mock()
        resp.read.side_effect = [0,[FAKES.templatepool, FAKES.imagepool],0]
        mock_open.return_value = resp
        self.assertDictEqual(self.expected_images,
                             self.provider.get_images())

    @mock.patch('xmlrpccall')
    def test_get_filtered_images(self, mock_open):
        resp = mock.Mock()
        resp.read.side_effect = [0,[FAKES.templatepool, FAKES.imagepool],0]
        mock_open.return_value = resp
        self.provider.opts.vmcatcher_images = True
        filtered_images = {k: v for (k, v) in self.expected_images.items()
                           if v.get('image_marketplace_id')}
        self.assertDictEqual(filtered_images,
                             self.provider.get_images())

    def test_templates_missing(self):
        fake_dir = uuid.uuid4().hex
        self.provider.opts.template_dir = fake_dir
        self.assertRaises(OSError, self.provider.get_templates)

    def test_load_templates(self): 
	# TBD
        pass
