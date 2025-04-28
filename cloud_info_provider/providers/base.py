import logging

import yaml

from cloud_info_provider import glue
from cloud_info_provider.exceptions import CloudInfoException
from cloud_info_provider.providers import utils


class BaseProvider:
    goc_service_type = ""
    interface_name = ""

    def _load_site_config(self, config_file):
        with open(config_file, "r") as f:
            self.site_config = yaml.load(f.read(), Loader=yaml.SafeLoader)

        # Ensure the file has what we need
        for field in ("gocdb", "endpoint", "vos"):
            if field not in self.site_config:
                raise CloudInfoException("{field} not available in site config")

    def __init__(self, opts, **kwargs):
        self.opts = opts
        self.setup_logging()
        self._load_site_config(opts.site_config)
        self._goc_info = {}
        self._ca_info = {}
        self.service = None
        self.manager = None
        self.endpoint = None

    def _get_ca_info(self, url):
        if url not in self._ca_info:
            ca_info = utils.get_endpoint_ca_information(url, self.opts.insecure)
            self._ca_info[url] = ca_info
        return self._ca_info[url]

    def _get_goc_info(self, url):
        if url not in self._goc_info:
            # pylint: disable=no-member
            self._goc_info[url] = utils.find_in_gocdb(
                url, self.goc_service_type, self.opts.insecure, self.opts.timeout
            )
        return self._goc_info[url]

    def fetch(self):
        self.get_service()
        self.get_manager()
        self.get_endpoint()
        r = [self.service, self.manager, self.endpoint]
        r.extend(self.get_shares())
        return r

    def get_service_id(self):
        return "service"

    def get_manager_id(self):
        return "manager"

    def get_endpoint_id(self):
        return "endpoint"

    def get_service(self):
        site_name = self.site_config["gocdb"]
        svc_id = self.get_service_id()
        name = f"Cloud Compute service at {site_name}"
        status_info = (
            f"https://argo.egi.eu/egi/report-status/Critical/SITES/{site_name}"
        )
        other_info = self._get_goc_info(self.site_config["endpoint"])
        svc = glue.CloudComputingService(
            id=svc_id, name=name, status_info=status_info, other_info=other_info
        )
        svc.add_association("AdminDomain", site_name)
        self.service = svc
        return self.service

    def get_manager(self):
        mgr_id = self.get_manager_id()
        mgr = glue.CloudComputingManager(id=mgr_id)
        mgr.add_associated_object(self.service)
        self.manager = mgr
        return self.manager

    def get_endpoint(self):
        ept_id = self.get_endpoint_id()
        ept = glue.CloudComputingEndpoint(id=ept_id, interface_name=self.interface_name)
        ept.add_associated_object(self.service)
        ept.health_state = "ok"
        ept.health_state_info = "Endpoint funtioning properly."
        ca_info = self._get_ca_info(self.site_config["endpoint"])
        if "issuer" in ca_info:
            ept.issuer_ca = ca_info["issuer"]
        if "trusted_cas" in ca_info:
            ept.trusted_cas = ca_info["trusted_cas"]
        ept.downtime_info = (
            "https://goc.egi.eu/portal/index.php?"
            f"Page_Type=Downtimes_Calendar&site={self.site_config['gocdb']}"
        )
        self.endpoint = ept
        return self.endpoint

    def get_shares(self):
        return []

    def setup_logging(self):
        level = logging.DEBUG if self.opts.debug else logging.INFO
        logging.basicConfig(level=level)

    @staticmethod
    def populate_parser(parser):
        """Populate the argparser 'parser' with the needed options."""
        parser.add_argument(
            "site_config",
            help="YAML file with site configuration (as in fedcloud-catchall-ops)",
        )
