"""
Tests for the publishers
"""

from __future__ import print_function

import argparse
import json

import mock
import six
from cloud_info_provider.publishers import ams, stdout
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

    def test_get_ams_cert(self):
        class Opts(object):
            ams_host = "example.com"
            ams_project = "foobar"
            ams_token = None
            ams_cert = "foo"
            ams_key = "bar"

        opts = Opts()
        publisher = ams.AMSPublisher(opts)
        with mock.patch("cloud_info_provider.publishers.ams.ArgoMessagingService") as m_ams:
            publisher._get_ams()
            m_ams.assert_called_with(endpoint=opts.ams_host,
                                     project=opts.ams_project,
                                     cert=opts.ams_cert,
                                     key=opts.ams_key)

    def test_get_ams_token(self):
        class Opts(object):
            ams_host = "example.com"
            ams_project = "foobar"
            ams_token = "12445"

        opts = Opts()
        publisher = ams.AMSPublisher(opts)
        with mock.patch("cloud_info_provider.publishers.ams.ArgoMessagingService") as m_ams:
            publisher._get_ams()
            m_ams.assert_called_with(endpoint=opts.ams_host,
                                     project=opts.ams_project,
                                     token=opts.ams_token)


    def test_publish(self):
        class Opts(object):
            ams_host = "example.com"
            ams_topic = "topic"
            ams_project = "bar"
            ams_token = "000"

        opts = Opts()
        publisher = ams.AMSPublisher(opts)
        output = "foo"
        with utils.nested(
            mock.patch("cloud_info_provider.publishers.ams.ArgoMessagingService"),
            mock.patch("cloud_info_provider.publishers.ams.AmsMessage")
        ) as (m_ams, m_msg):
            publisher.publish(output)
            m_ams.assert_called_with(endpoint=opts.ams_host,
                                     project=opts.ams_project,
                                     token=opts.ams_token)
            m_msg.assert_called_with(data="foo", attributes={})
            m_ams.return_value.publish.assert_called_with(opts.ams_topic,
                                                          m_msg.return_value)
