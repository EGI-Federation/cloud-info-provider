"""
Simple utilities for getting information from endpoints
"""

import logging
import socket
from urllib.parse import urlparse
from xml.etree.ElementTree import ParseError  # nosec

import defusedxml.ElementTree
import requests
from OpenSSL import SSL

logger = logging.getLogger(__name__)


def _are_url_similar(u1, u2):
    """Compares 2 urls just considering host and path"""
    if u1[0:2] == u2[0:2]:
        # consider path/ == path which is not strictly the same
        # but good enough for our case
        p1 = u1[2].strip("/")
        p2 = u2[2].strip("/")
        if p1 == p2:
            return True
    return False


def _find_url_in_result(svc_url, result):
    """Finds service matching URL in GOCDB

    Parses XML gotten from GOC and tries to find the service which
    matches the URL of the service. It returns a dictionary with keys
    `gocdb_id` which has the ID in GOCDB of the service and `site_name`
    with the name of the site. If no match is found, an empty dictionary
    is returned.
    """

    svc_url = urlparse(svc_url)
    for svc in result:
        urls = []
        try:
            urls.append(urlparse(svc.find("URL").text))
        except AttributeError:
            # something is wrong at GOCDB, do not care
            pass
        for ep in svc.find("ENDPOINTS"):
            try:
                urls.append(urlparse(ep.find("URL").text))
            except AttributeError:
                # something is wrong at GOCDB, do not care
                pass
        for url in urls:
            if _are_url_similar(svc_url, url):
                return {
                    "gocdb_id": svc.attrib["PRIMARY_KEY"],
                    "site_name": svc.find("SITENAME").text,
                }
    logger.warning("Unable to find URL %s in GOCDB!", svc_url)
    return {}


def find_in_gocdb(svc_url, svc_type, insecure=False, timeout=None):
    """Find service matching URL and service type in GOCDB"""

    verify = not insecure
    r = requests.get(
        "https://goc.egi.eu/gocdbpi/public/",
        params={"method": "get_service", "service_type": svc_type},
        verify=verify,
        timeout=timeout,
    )
    if r.status_code != 200:
        logger.warning("Something went wrong with GOC %s", r.text)
        return {}
    try:
        goc_xml = defusedxml.ElementTree.fromstring(r.text)
        return _find_url_in_result(svc_url, goc_xml)
    except ParseError:
        logger.warning("Something went wrong with parsing GOC output")
        return {}


def get_dn(x509name):
    """Return the DN of an X509Name object."""
    # str(X509Name) is something like <X509Name object 'DN'>
    obj_name = str(x509name)
    start = obj_name.find("'") + 1
    end = obj_name.rfind("'")
    return obj_name[start:end]


def get_endpoint_ca_information(endpoint_url, insecure=False):
    """Return certificate issuer and trusted CAs list of HTTPS endpoint."""
    ca_info = {"issuer": "UNKNOWN", "trusted_cas": ["UNKNOWN"]}

    verify = SSL.VERIFY_NONE if insecure else SSL.VERIFY_PEER

    scheme = urlparse(endpoint_url).scheme
    host = urlparse(endpoint_url).hostname
    port = urlparse(endpoint_url).port

    if scheme != "https":
        return ca_info

    # use default port for https
    if not port:
        port = 443

    try:
        ctx = SSL.Context(SSL.TLSv1_2_METHOD)
        ctx.set_options(SSL.OP_NO_SSLv2)
        ctx.set_options(SSL.OP_NO_SSLv3)
        ctx.set_verify(verify, lambda conn, cert, errno, depth, ok: ok)
        ctx.set_default_verify_paths()

        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((host, port))

        client_ssl = SSL.Connection(ctx, client)
        client_ssl.set_connect_state()
        client_ssl.set_tlsext_host_name(host.encode("utf-8"))
        client_ssl.do_handshake()

        cert = client_ssl.get_peer_certificate()
        issuer = get_dn(cert.get_issuer())

        client_ca_list = client_ssl.get_client_ca_list()
        trusted_cas = [get_dn(ca) for ca in client_ca_list]

        client_ssl.shutdown()
        client_ssl.close()

        ca_info["issuer"] = issuer
        ca_info["trusted_cas"] = trusted_cas
    except SSL.Error as e:
        logger.warning("Issue when getting CA info from endpoint: %s", e)
    except TimeoutError as e:
        logger.warning("Timeout when getting CA info from endpoint: %s", e)

    return ca_info
