import requests
import urllib3
from cloud_info_provider import exceptions, utils
from cloud_info_provider.providers import base, static


class MesosProvider(base.BaseProvider):
    service_type = "compute"
    goc_service_type = None

    def __init__(self, opts, **kwargs):
        super(MesosProvider, self).__init__(opts, **kwargs)

        if not opts.mesos_endpoint:
            msg = (
                "You must provide a Mesos, Marathon or Chronos API "
                "endpoint via --mesos-endpoint (alternatively using "
                "the environment variable MESOS_ENDPOINT)"
            )
            raise exceptions.MesosProviderException(msg)

        if not opts.mesos_framework:
            msg = "You must provide the endpoint URL to connect to"
            raise exceptions.MesosProviderException(msg)

        self.framework_url = opts.mesos_endpoint
        self.api_endpoints = []
        self.insecure = opts.insecure
        self.cacert = opts.mesos_cacert
        if self.insecure:
            # requests.packages.urllib3.disable_warnings()
            urllib3.disable_warnings()
            self.cacert = False

        if opts.mesos_framework == "mesos":
            self.api_endpoints = ["/metrics/snapshot", "state"]
        elif opts.mesos_framework == "marathon":
            self.api_endpoints = ["v2/info", "v2/leader"]
        self.goc_service_type = "eu.indigo-datacloud.%s" % opts.mesos_framework

        self.static = static.StaticProvider(opts)

        self.headers = {}
        if opts.oidc_token:
            self.headers["Authorization"] = "Bearer %s" % opts.oidc_token

    def get_site_info(self, **kwargs):
        _fields = (
            "name",
            "is_public",
            "id",
            "country",
            "country_code",
            "roc",
            "subgrid",
            "giis_url",
        )
        return self.static.get_site_info(fields=_fields)

    def get_compute_endpoints(self, **kwargs):
        def _update(old, new):
            old.update((k, v) for k, v in new.items() if v not in ["null", None])

        ret = {
            "endpoints": {self.framework_url: {}},
            "compute_service_name": self.framework_url,
        }

        # gather & update default (compute) values
        defaults = self.static.get_compute_endpoint_defaults(prefix=True)
        _update(ret["endpoints"][self.framework_url], defaults)

        # gather & update only relevant static data (global & endpoint levels)
        _global_fields = (
            "service_parent_id",
            "accelerators",
            "total_accelerators",
            "total_cores",
            "total_ram",
            "local_volumes_host_base_path",
            "persistent_storage_drivers",
            "load_balancer_ips",
        )
        _endpoint_fields = _global_fields
        static_info = self.static.get_compute_endpoints(
            global_fields=_global_fields, endpoint_fields=_endpoint_fields
        )
        try:
            static_info_endpoint = static_info.pop("endpoints")[self.framework_url]
        except KeyError:
            static_info_endpoint = {}
        _update(static_info, static_info_endpoint)
        _update(ret["endpoints"][self.framework_url], static_info)

        # gather & update dynamic info
        for api_endp in self.api_endpoints:
            api_url = "/".join([self.framework_url, api_endp])
            r = requests.get(
                api_url,
                headers=self.headers,
                verify=self.cacert,
                timeout=self.opts.timeout,
            )
            if r.status_code == requests.codes["ok"]:
                _update(ret["endpoints"][self.framework_url], r.json())
            else:
                msg = "Request failed: %s" % r.content
                raise exceptions.MesosProviderException(msg)

        return ret

    @staticmethod
    def populate_parser(parser):
        parser.add_argument(
            "--insecure",
            action="store_true",
            help=(
                'Explicitly allow to perform "insecure" '
                "SSL (https) requests. The server's certificate will "
                "not be verified against any certificate authorities. "
                "This option should be used with caution."
            ),
        )
        parser.add_argument(
            "--mesos-framework",
            choices=["mesos", "marathon", "chronos"],
            help=("Select the type of framework to collect data from (required)."),
        )
        parser.add_argument(
            "--mesos-endpoint",
            metavar="<api-url>",
            default=utils.env("MESOS_ENDPOINT"),
            help=(
                "Specify Mesos|Marathon API endpoint. "
                "Defaults to env[MESOS_ENDPOINT]"
            ),
        )
        parser.add_argument(
            "--mesos-cacert",
            metavar="<ca-certificate>",
            default=utils.env("MESOS_ENDPOINT"),
            help=(
                "Specify a CA bundle file to verify HTTPS connections "
                "to Mesos endpoints."
            ),
        )
        parser.add_argument(
            "--oidc-auth-bearer-token",
            metavar="<bearer-token>",
            default=utils.env("ACCESS_BEARER_TOKEN"),
            dest="oidc_token",
            help=(
                "Specify OIDC bearer token to use when "
                "authenticating with the API. Defaults "
                "to env[ACCESS_BEARER_TOKEN]"
            ),
        )
