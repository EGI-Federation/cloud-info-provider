import requests
from cloud_info_provider import exceptions, utils
from cloud_info_provider.providers import base, static


class OnedataProvider(base.BaseProvider):
    service_type = "storage"
    goc_service_type = None

    def __init__(self, opts, **kwargs):
        super(OnedataProvider, self).__init__(opts, **kwargs)

        if not opts.onezone_api_url:
            msg = (
                "You must provide a OneData API endpoint via "
                "--onedata-endpoint (alternatively using the "
                "environment variable ONEZONE_API_URL)"
            )
            raise exceptions.OnedataProviderException(msg)

        self.onezone_api_url = opts.onezone_api_url
        self.goc_service_type = "eu.egi.cloud.storage-management.oneprovider"

        self.static = static.StaticProvider(opts)

        self.headers = {}
        if opts.oidc_token:
            self.headers["X-Auth-Token"] = "%s: %s" % (
                opts.oidc_idp_prefix,
                opts.oidc_token,
            )

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

    def get_oneproviders_from_onezone(self):
        def _do_request(url):
            r = requests.get(url, headers=self.headers, timeout=self.opts.timeout)
            if r.status_code == requests.codes["ok"]:
                return r.json()
            else:
                msg = "Request failed: %s" % r.content
                raise exceptions.OnedataProviderException(msg)

        _url = "/".join([self.onezone_api_url, "onezone/providers"])
        try:
            oneprov_ids = _do_request(_url)["providers"]
        except KeyError:
            oneprov_ids = []
        d = {}
        for oneprov_id in oneprov_ids:
            _oneprov_url = "/".join([_url, oneprov_id])
            try:
                _domain = _do_request(_oneprov_url)["domain"]
                d[_domain] = {"id": oneprov_id}
            except KeyError:
                raise exceptions.OnedataProviderException(
                    ("Cannot get Oneprovider domains from Onezone")
                )
        return d

    def get_storage_endpoints(self, **kwargs):
        d_onezone = self.get_oneproviders_from_onezone()

        defaults = self.static.get_storage_endpoint_defaults(prefix=True)
        defaults_endpoint = self.static.get_storage_endpoints()
        try:
            endp_data = defaults_endpoint.pop("endpoints")
        except KeyError:
            raise exceptions.OnedataProviderException(
                ("Static configuration file does not contain Oneprovider endpoints")
            )
        defaults_endpoint.update(defaults)

        d_endp = {}
        for oneprov_domain, oneprov_data in endp_data.items():
            d_endp[oneprov_domain] = {}
            try:
                oneprov_id = d_onezone[oneprov_domain]["id"]
            except KeyError:
                continue
            d_endp[oneprov_domain]["onedata_id"] = oneprov_id
            d_endp[oneprov_domain]["goc_service_type"] = self.goc_service_type
            aux = oneprov_data.copy()
            aux.update(defaults_endpoint)
            d_endp[oneprov_domain].update(aux)
        return {"endpoints": d_endp}

    @staticmethod
    def populate_parser(parser):
        parser.add_argument(
            "--onezone-api-url",
            metavar="<api-url>",
            default=utils.env("ONEZONE_API_URL"),
            help=(
                "Specify OneData API endpoint with format: "
                "https://onezone.example.org/api/v3. "
                "Defaults to env[ONEZONE_API_URL]"
            ),
        )
        parser.add_argument(
            "--oidc-x-auth-token",
            metavar="<x-auth-token>",
            default=utils.env("ACCESS_BEARER_TOKEN"),
            dest="oidc_token",
            help=(
                "Specify OIDC X-Auth token to use when "
                "authenticating with the API. Defaults "
                "to env[ACCESS_BEARER_TOKEN]"
            ),
        )
        parser.add_argument(
            "--oidc-idp-prefix",
            metavar="<idp-prefix>",
            dest="oidc_idp_prefix",
            help=("Specify OIDC X-Auth IdP prefix for the X-Auth token"),
        )
