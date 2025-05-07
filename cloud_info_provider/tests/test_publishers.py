"""
Tests for the publishers
"""

from __future__ import print_function

import mock
from cloud_info_provider.publishers import stdout
from cloud_info_provider.tests import base


class StdOutPublisherTest(base.TestCase):
    def test_publish(self):
        publisher = stdout.StdOutPublisher(None)
        output = "foo"
        with mock.patch("builtins.print") as m_print:
            publisher.publish(output)
            m_print.assert_called_with(output)
