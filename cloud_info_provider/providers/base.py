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
        self.objs = {}

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

    def add_glue(self, o):
        class_name = o.__class__.__name__
        objs = self.objs.get(class_name, [])
        objs.append(o)
        self.objs[class_name] = objs

    def get_first_obj(self, obj_type):
        o = self.objs.get(obj_type, [None])
        return o[0]

    def get_objs(self, obj_type):
        return self.objs.get(obj_type, [])

    @property
    def service(self):
        return self.get_first_obj("CloudComputingService")

    @property
    def manager(self):
        return self.get_first_obj("CloudComputingManager")

    @property
    def endpoint(self):
        return self.get_first_obj("CloudComputingEndpoint")

    def fetch(self):
        self.build_service()
        self.build_manager()
        self.build_endpoint()
        self.build_shares()
        share_count = len(self.objs.get("Share", []))
        svc = self.service
        if svc:
            svc.complexity = f"endpointType=1,share={share_count}"
        return self.objs

    def get_service_id(self):
        return "service"

    def get_manager_id(self):
        return "manager"

    def get_endpoint_id(self):
        return "endpoint"

    def build_service(self, **kwargs):
        site_name = self.site_config["gocdb"]
        service_defaults = {
            "id": self.get_service_id(),
            "name": f"Cloud Compute service at {site_name}",
            "status_info": (
                f"https://argo.egi.eu/egi/report-status/Critical/SITES/{site_name}"
            ),
            "other_info": self._get_goc_info(self.site_config["endpoint"]),
        }
        service_defaults.update(kwargs)
        svc = glue.CloudComputingService(**service_defaults)
        svc.add_association("AdminDomain", site_name)
        self.add_glue(svc)
        return svc

    def build_manager(self, **kwargs):
        manager_defaults = {"id": self.get_manager_id()}
        manager_defaults.update(kwargs)
        mgr = glue.CloudComputingManager(**manager_defaults)
        mgr.add_associated_object(self.service)
        self.add_glue(mgr)
        return mgr

    def build_endpoint(self, **kwargs):
        ept_defaults = {
            "id": self.get_endpoint_id(),
            "name": f"Cloud computing endpoint for {self.get_endpoint_id()}",
            "interface_name": self.interface_name,
            "url": self.site_config["endpoint"],
            "health_state": "ok",
            "health_state_info": "Endpoint functioning properly",
            "downtime_info": (
                f"https://goc.egi.eu/portal/index.php?Page_Type=Downtimes_Calendar&site={self.site_config['gocdb']}"
            ),
        }
        ca_info = self._get_ca_info(self.site_config["endpoint"])
        if "issuer" in ca_info:
            ept_defaults["issuer_ca"] = ca_info["issuer"]
        if "trusted_cas" in ca_info:
            ept_defaults["trusted_cas"] = ca_info["trusted_cas"]
        ept_defaults.update(kwargs)
        ept = glue.CloudComputingEndpoint(**ept_defaults)
        ept.add_associated_object(self.service)
        self.add_glue(ept)
        return ept

    def build_shares(self):
        pass

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
