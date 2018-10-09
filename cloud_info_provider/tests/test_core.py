import os.path

import mock

import cloud_info_provider.core
from cloud_info_provider.tests import base
from cloud_info_provider.tests import data
from cloud_info_provider.tests import utils

DATA = data.DATA


class ModuleTest(base.TestCase):
    def test_main(self):
        with utils.nested(
            mock.patch.object(cloud_info_provider.core, 'parse_opts'),
            mock.patch('cloud_info_provider.core.CloudBDII'),
            mock.patch('cloud_info_provider.core.ComputeBDII'),
            mock.patch('cloud_info_provider.core.StorageBDII')
        ) as (m0, m1, m2, m3):
            m0.return_value = None
            for i in (m1, m2, m3):
                i = i.return_value
                i.render.return_value = 'foo'

            self.assertIsNone(cloud_info_provider.core.main())

            for i in (m0, m1, m2, m3):
                self.assertTrue(i.called)


class FakeBDIIOpts(object):
    middleware = 'foo middleware'
    yaml_file = None
    template_dir = ''
    template_extension = ''


class FakeProvider(object):
    def __init__(self, opts):
        pass

    def method(self):
        pass


class BaseTest(base.TestCase):
    def setUp(self):
        super(BaseTest, self).setUp()

        cloud_info_provider.core.SUPPORTED_MIDDLEWARE = {
            'static': 'cloud_info_provider.tests.test_core.FakeProvider',
            'foo middleware': 'cloud_info_provider.tests.test_core.'
                              'FakeProvider',
        }

        self.opts = FakeBDIIOpts()
        cwd = os.path.dirname(__file__)
        template_dir = os.path.join(cwd, '..', '..', 'etc', 'templates')
        self.opts.template_dir = template_dir


class BaseBDIITest(BaseTest):
    def test_get_info_from_providers(self):
        cases = (
            (
                {},
                {},
                {}
            ),
            (
                {'foo': 'bar'},
                {'bar': 'bazonk'},
                {'foo': 'bar', 'bar': 'bazonk'},
            ),
            (
                {'foo': 'bar'},
                {'foo': 'bazonk'},
                {'foo': 'bazonk'},
            ),
            (
                {},
                {'foo': 'bazonk'},
                {'foo': 'bazonk'},
            ),
            (
                {'foo': 'bar'},
                {},
                {'foo': 'bar'},
            ),
        )

        bdii = cloud_info_provider.core.BaseBDII(self.opts)

        for s, d, e in cases:
            with utils.nested(
                mock.patch.object(bdii.static_provider, 'method'),
                mock.patch.object(bdii.dynamic_provider, 'method')
            ) as (m_static, m_dynamic):
                m_static.return_value = s
                m_dynamic.return_value = d

                self.assertEqual(e, bdii._get_info_from_providers('method'))

    def test_load_templates(self):
        self.opts.template_dir = 'foobar'
        tpls = ('foo', 'bar')
        expected_tpls = {
            'foo': 'foobar/foo.%s' % self.opts.template_extension,
            'bar': 'foobar/bar.%s' % self.opts.template_extension
        }

        bdii = cloud_info_provider.core.BaseBDII(self.opts)
        with utils.nested(
                mock.patch.object(bdii, 'templates', tpls)):
            bdii.load_templates()
            templates_files = bdii.__dict__['templates_files']
            self.assertEqual(templates_files, expected_tpls)

    def test_format_template(self):
        self.opts.template_dir = 'foobar'
        tpl_contents = 'foo ${attributes["fobble"]}'
        tpl_files = {
            'foo': 'foobar/foo.%s' % self.opts.template_extension,
            'bar': 'foobar/bar.%s' % self.opts.template_extension
        }
        info = {'fobble': 'burble', 'brongle': 'farbla'}
        expected = 'foo burble'

        bdii = cloud_info_provider.core.BaseBDII(self.opts)
        with utils.nested(
                mock.patch.object(bdii, 'templates_files', tpl_files),
                mock.patch('mako.util.open',
                           mock.mock_open(read_data=tpl_contents), create=True)
        ):
            self.assertEqual(expected, bdii._format_template('foo', info))


class CloudBDIITest(BaseTest):
    @mock.patch.object(cloud_info_provider.core.BaseBDII, '_format_template')
    @mock.patch.object(cloud_info_provider.core.CloudBDII,
                       '_get_info_from_providers')
    def test_render(self, m_get_info, m_format):
        m_get_info.return_value = DATA.site_info
        m_format.return_value = 'foo'
        bdii = cloud_info_provider.core.CloudBDII(self.opts)
        self.assertIsNotNone(bdii.render())
        m_format.assert_has_calls([mock.call("headers",
                                  DATA.site_info),
                                  mock.call("clouddomain", DATA.site_info)])


class StorageBDIITEst(BaseTest):
    @mock.patch.object(cloud_info_provider.core.BaseBDII, '_format_template')
    @mock.patch.object(cloud_info_provider.core.StorageBDII,
                       '_get_info_from_providers')
    def test_render(self, m_get_info, m_format):
        m_get_info.side_effect = (
            DATA.storage_endpoints,
            DATA.site_info
        )
        m_format.return_value = 'foo'
        endpoints = DATA.storage_endpoints
        static_storage_info = dict(endpoints, **DATA.site_info)
        static_storage_info.pop('endpoints')

        for endpoint in endpoints['endpoints'].values():
            endpoint.update(static_storage_info)

        info = {}
        info.update({'endpoints': endpoints})
        info.update({'static_storage_info': static_storage_info})

        bdii = cloud_info_provider.core.StorageBDII(self.opts)
        self.assertIsNotNone(bdii.render())

        m_format.assert_has_calls([mock.call("storage", info)])

    @mock.patch.object(cloud_info_provider.core.StorageBDII,
                       '_get_info_from_providers')
    def test_render_empty(self, m_get_info):
        m_get_info.side_effect = (
            {},
            DATA.site_info
        )
        bdii = cloud_info_provider.core.StorageBDII(self.opts)
        self.assertEqual('', bdii.render())


class ComputeBDIITest(BaseTest):

    @mock.patch.object(cloud_info_provider.core.BaseBDII, '_format_template')
    @mock.patch.object(cloud_info_provider.core.ComputeBDII,
                       '_get_info_from_providers')
    def test_render(self, m_get_info, m_format):

        def get_info_side_effect(what, **kwargs):
            data_mapping = {
                'get_site_info': DATA.site_info,
                'get_compute_shares': DATA.compute_shares,
                'get_compute_endpoints': DATA.compute_endpoints,
                'get_images': DATA.compute_images,
                'get_templates': DATA.compute_templates,
                'get_instances': {},
                'get_compute_quotas': {},
            }
            return data_mapping[what]

        m_get_info.side_effect = get_info_side_effect
        m_format.return_value = 'foo'
        endpoints = DATA.compute_endpoints
        static_compute_info = dict(endpoints, **DATA.site_info)
        static_compute_info.pop('endpoints')
        templates = DATA.compute_templates
        images = DATA.compute_images
        shares = DATA.compute_shares

        for endpoint in endpoints['endpoints'].values():
            endpoint.update(static_compute_info)

        for template in templates.values():
            template.update(static_compute_info)

        for image in images.values():
            image.update(static_compute_info)

        for share in shares.values():
            share.update({"endpoints": endpoints,
                          "images": images,
                          "templates": templates,
                          "instances": {},
                          "quotas": {}})

        info = {}
        info.update({'static_compute_info': static_compute_info})
        info.update({'shares': shares})

        bdii = cloud_info_provider.core.ComputeBDII(self.opts)
        self.assertIsNotNone(bdii.render())

        m_format.assert_has_calls([mock.call("compute", info)])

    @mock.patch.object(cloud_info_provider.core.ComputeBDII,
                       '_get_info_from_providers')
    def test_render_empty(self, m_get_info):
        m_get_info.side_effect = (
            DATA.site_info,
            DATA.compute_shares,
            {},
            DATA.site_info,
            DATA.compute_shares,
            {},
        )
        bdii = cloud_info_provider.core.ComputeBDII(self.opts)
        self.assertFalse(bdii.render())
        self.assertEqual('', bdii.render())
