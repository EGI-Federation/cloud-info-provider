"""
Argo Messaging System Publisher

Publishes the cloud-info to a topic in the AMS.
"""


import base64
import json
import logging

import requests

from cloud_info_provider.publishers.base import BasePublisher


class AMSPublisher(BasePublisher):
    @staticmethod
    def populate_parser(parser):
        parser.add_argument(
            "--ams-token", metavar="<token>", help="Token for AMS authentication"
        )

        parser.add_argument(
            "--ams-host", metavar="<host>", default="msg.argo.grnet.gr", help="AMS host"
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

    def _get_ams_token(self):
        if self.opts.ams_token:
            return self.opts.ams_token

        url = "https://{0}:8443/v1/service-types/ams/hosts/" "{0}:authx509".format(
            self.opts.ams_host
        )

        r = requests.get(url, cert=(self.opts.ams_cert, self.opts.ams_key))
        return r.json()["token"]

    def publish(self, output):
        token = self._get_ams_token()
        url = "https://{0}/v1/projects/{2}/topics/{3}" ":publish?key={1}".format(
            self.opts.ams_host, token, self.opts.ams_project, self.opts.ams_topic
        )
        payload = base64.b64encode(output.encode("utf-8")).decode("utf-8")
        data = {"messages": [{"attributes": {}, "data": payload}]}
        r = requests.post(
            url, headers={"content-type": "application/json"}, data=json.dumps(data)
        )
        r.raise_for_status()
        logging.info(
            "Published msg at: %s, message id: %s",
            self.opts.ams_topic,
            " ".join(r.json()["messageIds"]),
        )
