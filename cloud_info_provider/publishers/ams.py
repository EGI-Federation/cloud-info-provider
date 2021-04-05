"""
Argo Messaging System Publisher

Publishes the cloud-info to a topic in the AMS.
"""


import base64
import json
import logging

import requests
from argo_ams_library import AmsMessage, ArgoMessagingService
from cloud_info_provider.publishers.base import BasePublisher

class AMSPublisher(BasePublisher):
    @staticmethod
    def populate_parser(parser):
        parser.add_argument(
            "--ams-token", metavar="<token>", help="Token for AMS authentication"
        )

        parser.add_argument(
            "--ams-host",
            metavar="<host>",
            default="msg.argo.grnet.gr",
            help="AMS host",
        )

        # XXX this should be discovered
        parser.add_argument("--ams-topic", metavar="<topic>", help="AMS topic")

        parser.add_argument(
            "--ams-project",
            metavar="<project>",
            default="egi_cloud_info",
            help="AMS project",
        )

        parser.add_argument(
            "--ams-cert",
            metavar="<certfile>",
            help="Certificate file for AMS authentication",
        )

        parser.add_argument(
            "--ams-key", metavar="<keyfile>", help="Key file for AMS authentication"
        )

    def _get_ams(self):
        if self.opts.ams_token:
            return ArgoMessagingService(endpoint=self.opts.ams_host,
                                        project=self.opts.ams_project,
                                        token=self.opts.ams_token)
        else:
            return ArgoMessagingService(endpoint=self.opts.ams_host,
                                        project=self.opts.ams_project,
                                        cert=self.opts.ams_cert,
                                        key=self.opts.ams_key)

    def publish(self, output):
        ams = self._get_ams()
        msg = AmsMessage(data=output, attributes={})
        ret = ams.publish(self.opts.ams_topic, msg)
        logging.info(
            "Published msg at: %s, message id: %s",
            self.opts.ams_topic,
            " ".join(ret["messageIds"]),
        )
