import mock
from cloud_info_provider import core
from cloud_info_provider.tests import base


class CoreOptionsTest(base.TestCase):
    def test_populate_parser(self):
        providers = {"foo": mock.Mock()}
        formatters = ["foobar"]
        publishers = {"boom": mock.Mock()}
        parser = core.get_parser(providers, formatters, publishers)
        opts = parser.parse_args(
            [
                "--middleware",
                "foo",
                "--format",
                "foobar",
                "--publisher",
                "boom",
                "--debug",
            ]
        )
        self.assertEqual(opts.middleware, "foo")
        self.assertEqual(opts.format, "foobar")
        self.assertEqual(opts.publisher, "boom")
        self.assertEqual(opts.debug, True)

    def test_populate_parser_defaults(self):
        parser = core.get_parser({}, [], {})
        opts = parser.parse_args([])
        self.assertEqual(opts.middleware, "openstack")
        self.assertEqual(opts.format, "glue21json")
        self.assertEqual(opts.publisher, "stdout")
        self.assertEqual(opts.debug, False)
