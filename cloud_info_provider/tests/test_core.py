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
        assert opts.middleware == "foo"
        assert opts.format == "foobar"
        assert opts.publisher == "boom"
        assert opts.debug

    def test_populate_parser_defaults(self):
        parser = core.get_parser({}, [], {})
        opts = parser.parse_args([])
        assert opts.middleware == "openstack"
        assert opts.format == "glue21json"
        assert opts.publisher == "stdout"
        assert not opts.debug
