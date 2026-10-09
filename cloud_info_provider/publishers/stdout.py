"""
StdOut Publisher

Just prints to stdout
"""

import json
from io import StringIO

from cloud_info_provider.publishers.base import BasePublisher


class StdOutPublisher(BasePublisher):
    @staticmethod
    def populate_parser(parser):
        """Populate the argparser 'parser' with the needed options."""

    def publish(self, output):
        print(output)


class JSONStdOutPublisher(BasePublisher):
    @staticmethod
    def populate_parser(parser):
        """Populate the argparser 'parser' with the needed options."""

    def publish(self, output):
        output_io = StringIO(output.replace("'", '"'))
        json_data = json.load(output_io)
        print(json.dumps(json_data, indent=4, sort_keys=True))
