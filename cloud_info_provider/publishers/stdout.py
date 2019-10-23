from __future__ import print_function

from cloud_info_provider.publishers.base import BasePublisher


class StdOutPublisher(BasePublisher):
    @staticmethod
    def populate_parser(parser):
        """Populate the argparser 'parser' with the needed options."""
        pass

    def publish(self, output):
        print(output)
