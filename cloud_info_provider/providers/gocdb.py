'''
Simple utilities for getting information fro GOCDB about the endpoints
'''
import logging


import defusedxml.ElementTree
import requests
from six.moves.urllib.parse import urlparse
from xml.etree.ElementTree import ParseError  # nosec


logger = logging.getLogger(__name__)


def _are_url_similar(u1, u2):
    '''Compares 2 urls just considering host and path'''
    if u1[0:2] == u2[0:2]:
        # consider path/ == path which is not strictly the same
        # but good enough for our case
        p1 = u1[2].strip('/')
        p2 = u2[2].strip('/')
        if p1 == p2:
            return True
    return False


def _find_url_in_result(svc_url, result):
    '''Finds service matching URL in GOCDB

       Parses XML gotten from GOC and tries to find the service which
       mathces the URL of the service. It returns a dictionary with keys
       `gocdb_id` which has the ID in GOCDB of the service and `site_name`
       with the name of the site. If no match is found, an empty dictionary
       is returned.
    '''

    svc_url = urlparse(svc_url)
    for svc in result:
        try:
            url = urlparse(svc.find('URL').text)
        except AttributeError:
            # something is wrong at GOCDB, skip this one
            continue
        if _are_url_similar(svc_url, url):
            return {'gocdb_id': svc.attrib['PRIMARY_KEY'],
                    'site_name': svc.find('SITENAME').text}
    logger.warning('Unable to find URL %s in GOCDB!', svc_url)
    return {}


def find_in_gocdb(svc_url, svc_type, insecure=False):
    '''Find service matching URL and service type in GOCDB'''

    verify = not insecure
    r = requests.get('https://goc.egi.eu/gocdbpi/public/',
                     params={'method': 'get_service',
                             'service_type': svc_type},
                     verify=verify)
    if r.status_code != 200:
        logger.warning("Something went wrong with GOC %s", r.text)
        return {}
    try:
        goc_xml = defusedxml.ElementTree.fromstring(r.text)
        return _find_url_in_result(svc_url, goc_xml)
    except ParseError:
        logger.warning('Something went wrong with parsing GOC output')
        return {}
