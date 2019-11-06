import mock

from cloud_info_provider import core
from cloud_info_provider.tests import base


class CoreOptionsTest(base.TestCase):
    def test_populate_parser(self):
        providers = {"foo": mock.Mock()}
        formatters = ["foobar"]
        auth_refreshers = {"bar": mock.Mock()}
        publishers = {"boom": mock.Mock()}
        parser = core.get_parser(providers, formatters, auth_refreshers, publishers)
        opts = parser.parse_args(
            [
                "--middleware",
                "foo",
                "--format",
                "foobar",
                "--auth-refresher",
                "bar",
                "--template-dir",
                "/baz",
                "--publisher",
                "boom",
                "--yaml-file",
                "/config.yaml",
                "--debug",
            ]
        )
        self.assertEqual(opts.middleware, "foo")
        self.assertEqual(opts.format, "foobar")
        self.assertEqual(opts.auth_refresher, "bar")
        self.assertEqual(opts.template_dir, "/baz")
        self.assertEqual(opts.yaml_file, "/config.yaml")
        self.assertEqual(opts.publisher, "boom")
        self.assertEqual(opts.debug, True)

    def test_populate_parser_defaults(self):
        parser = core.get_parser({}, [], {}, {})
        opts = parser.parse_args([])
        self.assertEqual(opts.middleware, "static")
        self.assertEqual(opts.format, "glue")
        self.assertEqual(opts.auth_refresher, None)
        self.assertEqual(opts.publisher, "stdout")
        self.assertEqual(opts.template_dir, "/etc/cloud-info-provider/templates")
        self.assertEqual(opts.yaml_file, "/etc/cloud-info-provider/static.yaml")
        self.assertEqual(opts.debug, False)
