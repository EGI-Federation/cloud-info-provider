import mock

import cloud_info_provider.formatters.base

from cloud_info_provider.tests import base
from cloud_info_provider.tests import utils


class BaseFormatterTest(base.BaseTest):
    def test_load_templates(self):
        self.opts.template_dir = 'foobar'
        tpls = ('foo', 'bar')
        expected_tpls = {
            'foo': 'foobar/foo.%s' % self.opts.template_extension,
            'bar': 'foobar/bar.%s' % self.opts.template_extension
        }

        base = cloud_info_provider.formatters.base.BaseFormatter()
        with utils.nested(
                mock.patch.object(base, 'templates', tpls)):
            base._load_templates(self.opts.template_dir)
            templates_files = base.__dict__['templates_files']
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

        base = cloud_info_provider.formatters.base.BaseFormatter()
        with utils.nested(
                mock.patch.object(base, 'templates_files', tpl_files),
                mock.patch('mako.util.open',
                           mock.mock_open(read_data=tpl_contents), create=True)
        ):
            self.assertEqual(expected, base._format_template('foo', info))
