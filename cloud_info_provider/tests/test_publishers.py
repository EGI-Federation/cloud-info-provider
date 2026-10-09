"""
Tests for the publishers
"""


from unittest import mock

from ..publishers import stdout
from . import base


class StdOutPublisherTest(base.TestCase):
    def test_publish(self):
        publisher = stdout.StdOutPublisher(None)
        output = "foo"
        with mock.patch("builtins.print") as m_print:
            publisher.publish(output)
            m_print.assert_called_with(output)
