"""
Tests for the publishers
"""

from __future__ import print_function

import argparse
import json
import mock

import six

from cloud_info_provider.publishers import ams
from cloud_info_provider.publishers import stdout
from cloud_info_provider.tests import base
from cloud_info_provider.tests import utils as utils


class StdOutPublisherTest(base.TestCase):
    def test_publish(self):
        publisher = stdout.StdOutPublisher(None)
        output = "foo"
        if six.PY2:
            with mock.patch("__builtin__.print") as m_print:
                publisher.publish(output)
                m_print.assert_called_with(output)
        else:
            with mock.patch("builtins.print") as m_print:
                publisher.publish(output)
                m_print.assert_called_with(output)


class AMSPublisherTest(base.TestCase):
    def test_populate_parser(self):
        parser = argparse.ArgumentParser(conflict_handler="resolve")
        ams.AMSPublisher.populate_parser(parser)
        opts = parser.parse_args(
            [
                "--ams-token",
                "foo",
                "--ams-host",
                "example.com",
                "--ams-topic",
                "foobar",
                "--ams-project",
                "bar",
                "--ams-cert",
                "baz",
                "--ams-key",
                "secret",
            ]
        )
        self.assertEqual("foo", opts.ams_token)
        self.assertEqual("example.com", opts.ams_host)
        self.assertEqual("foobar", opts.ams_topic)
        self.assertEqual("bar", opts.ams_project)
        self.assertEqual("baz", opts.ams_cert)
        self.assertEqual("secret", opts.ams_key)

    def test_get_token(self):
        class Opts(object):
            ams_host = "example.com"
            ams_token = None
            ams_cert = "foo"
            ams_key = "bar"

        publisher = ams.AMSPublisher(Opts())
        with mock.patch("requests.get") as m_get:
            r = mock.MagicMock()
            r.json.return_value = {"token": "secret"}
            m_get.return_value = r
            token = publisher._get_ams_token()
            url = (
                "https://example.com:8443/v1/service-types/ams/hosts/"
                "example.com:authx509"
            )
            m_get.assert_called_with(url, cert=("foo", "bar"))
            self.assertEqual("secret", token)

    def test_publish(self):
        class Opts(object):
            ams_host = "example.com"
            ams_topic = "topic"
            ams_project = "bar"

        publisher = ams.AMSPublisher(Opts())
        output = "foo"
        with utils.nested(
            mock.patch("requests.post"), mock.patch.object(publisher, "_get_ams_token")
        ) as (m_post, m_get_token):
            r = mock.MagicMock()
            m_post.return_value = r
            m_get_token.return_value = "secret"
            publisher.publish(output)
            data = {"messages": [{"attributes": {}, "data": "Zm9v"}]}
            url = (
                "https://example.com/v1/projects/bar/topics/" "topic:publish?key=secret"
            )
            headers = {"content-type": "application/json"}
            m_post.assert_called_with(url, headers=headers, data=json.dumps(data))
