import os.path
import unittest

import mock

import cloud_info.core
from cloud_info.tests import data
from cloud_info.tests import utils

DATA = data.DATA


class ModuleTest(unittest.TestCase):
    def test_main(self):
        with utils.nested(
            mock.patch.object(cloud_info.core, 'parse_opts'),
            mock.patch('cloud_info.core.CloudBDII'),
            mock.patch('cloud_info.core.ComputeBDII'),
            mock.patch('cloud_info.core.StorageBDII')
        ) as (m0, m1, m2, m3):
            m0.return_value = None
            for i in (m1, m2, m3):
                i = i.return_value
                i.render.return_value = 'foo'

            self.assertIsNone(cloud_info.core.main())

            for i in (m0, m1, m2, m3):
                assert i.called


class FakeBDIIOpts(object):
    full_bdii_ldif = False
    middleware = 'foo middleware'
    yaml_file = None
    template_dir = ''
    template_extension = ''


class BaseTest(unittest.TestCase):
    def setUp(self):
        cloud_info.core.SUPPORTED_MIDDLEWARE = {
            'static': mock.MagicMock(),
            'foo middleware': mock.MagicMock(),
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

        bdii = cloud_info.core.BaseBDII(self.opts)

        for s, d, e in cases:
            with utils.nested(
                mock.patch.object(bdii.static_provider, 'foomethod'),
                mock.patch.object(bdii.dynamic_provider, 'foomethod')
            ) as (m_static, m_dynamic):
                m_static.return_value = s
                m_dynamic.return_value = d

                self.assertEqual(e, bdii._get_info_from_providers('foomethod'))

    def test_load_templates(self):
        self.opts.template_dir = 'foobar'
        tpls = ('foo', 'bar')
        expected_tpls = {
            'foo': 'foobar/foo.%s' % self.opts.template_extension,
            'bar': 'foobar/bar.%s' % self.opts.template_extension
        }

        bdii = cloud_info.core.BaseBDII(self.opts)
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

        bdii = cloud_info.core.BaseBDII(self.opts)
        with utils.nested(
                mock.patch.object(bdii, 'templates_files', tpl_files),
                mock.patch('mako.util.open',
                           mock.mock_open(read_data=tpl_contents), create=True)
        ):
            self.assertEqual(expected, bdii._format_template('foo', info))


class CloudBDIITest(BaseTest):
    @mock.patch.object(cloud_info.core.BaseBDII, '_format_template')
    @mock.patch.object(cloud_info.core.CloudBDII, '_get_info_from_providers')
    def test_render(self, m_get_info, m_format):
        m_get_info.return_value = DATA.site_info
        m_format.return_value = 'foo'
        bdii = cloud_info.core.CloudBDII(self.opts)
        self.assertIsNotNone(bdii.render())
        m_format.assert_has_calls([mock.call("headers",
                                  DATA.site_info),
                                  mock.call("clouddomain", DATA.site_info)])

    @mock.patch.object(cloud_info.core.BaseBDII, '_format_template')
    @mock.patch.object(cloud_info.core.CloudBDII, '_get_info_from_providers')
    def test_render_full(self, m_get_info, m_format):
        self.opts.full_bdii_ldif = True
        m_get_info.return_value = DATA.site_info_full
        m_format.return_value = 'foo'
        bdii = cloud_info.core.CloudBDII(self.opts)
        self.assertIsNotNone(bdii.render())
        m_format.assert_has_calls([mock.call("headers", DATA.site_info_full),
                                  mock.call("domain", DATA.site_info_full),
                                  mock.call("bdii", DATA.site_info_full),
                                  mock.call("clouddomain",
                                            DATA.site_info_full)])


class StorageBDIITEst(BaseTest):
    @mock.patch.object(cloud_info.core.BaseBDII, '_format_template')
    @mock.patch.object(cloud_info.core.StorageBDII, '_get_info_from_providers')
    def test_render(self, m_get_info, m_format):
        m_get_info.side_effect = (
            DATA.storage_endpoints,
            DATA.site_info
        )
        m_format.return_value = 'foo'
        endpoints = DATA.storage_endpoints
        static_storage_info = dict(endpoints, **DATA.site_info)
        static_storage_info.pop('endpoints')

        bdii = cloud_info.core.StorageBDII(self.opts)
        self.assertIsNotNone(bdii.render())

        m_format_calls = [mock.call("storage_service", static_storage_info)]

        for url, endpoint in endpoints['endpoints'].items():
            endpoint.setdefault('endpoint_url', url)
            m_format_calls.append(mock.call('storage_endpoint',
                                  endpoint, extra=static_storage_info))

        m_format_calls.append(mock.call('storage_capacity',
                              static_storage_info))

        m_format.assert_has_calls(m_format_calls)

    @mock.patch.object(cloud_info.core.StorageBDII, '_get_info_from_providers')
    def test_render_empty(self, m_get_info):
        m_get_info.side_effect = (
            {},
            DATA.site_info
        )
        bdii = cloud_info.core.StorageBDII(self.opts)
        self.assertEqual('', bdii.render())


class ComputeBDIITest(BaseTest):
    @mock.patch.object(cloud_info.core.BaseBDII, '_format_template')
    @mock.patch.object(cloud_info.core.ComputeBDII, '_get_info_from_providers')
    def test_render(self, m_get_info, m_format):
        m_get_info.side_effect = (
            DATA.compute_endpoints,
            DATA.site_info,
            DATA.compute_templates,
            DATA.compute_images,
        )
        m_format.return_value = 'foo'
        endpoints = DATA.compute_endpoints
        static_compute_info = dict(endpoints, **DATA.site_info)
        static_compute_info.pop('endpoints')
        templates = DATA.compute_templates
        images = DATA.compute_images

        for url, endpoint in endpoints['endpoints'].items():
            endpoint.update(static_compute_info)

        for template_id, template in templates.items():
            template.update(static_compute_info)

        for image_id, image in images.items():
            image.update(static_compute_info)

        info = {}
        info.update({'endpoints': endpoints})
        info.update({'static_compute_info': static_compute_info})
        info.update({'templates': templates})
        info.update({'images': images})

        bdii = cloud_info.core.ComputeBDII(self.opts)
        self.assertIsNotNone(bdii.render())

        m_format.assert_has_calls([mock.call("compute_bdii", info)])

    @mock.patch.object(cloud_info.core.ComputeBDII, '_get_info_from_providers')
    def test_render_empty(self, m_get_info):
        m_get_info.side_effect = (
            {},
            DATA.site_info,
            DATA.compute_templates,
            DATA.compute_images,
        )
        bdii = cloud_info.core.ComputeBDII(self.opts)
        self.assertEqual('', bdii.render())
