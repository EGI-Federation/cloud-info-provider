#This provider is for an OpenNebula middleware. Part of the information is retreived from OpenNebula, the rest is provided via the static template. Note that this is a generic OpenNebula plugin. If you use rOCCI server on top of OpenNebula, please refer to the OpenNebulaROCCI provider

import os
import sys
import urllib2
from xml.dom import minidom

from cloud_bdii import providers

def env(*args, **kwargs):
    '''
    returns the first environment variable set
    if none are non-empty, defaults to '' or keyword arg default
    '''
    for arg in args:
        value = os.environ.get(arg, None)
        if value:
            return value
    return kwargs.get('default', '')


class OpenNebulaProvider(providers.BaseProvider):
    def __init__(self, opts):
        super(OpenNebulaProvider, self).__init__(opts)

	self.on_auth = opts.on_auth
	self.on_rpcxml_endpoint = opts.on_rpcxml_endpoint

	if not self.on_auth or self.on_auth is None:
	    f = open(os.path.expanduser('~')+'/.one/one_auth', 'w')
	    self.on_auth=f.read()
            f.close()

	if self.on_auth is None:
            print >> sys.stderr, ('ERROR, You must provide a on_auth '
                                  'via either --on-auth or env[ON_AUTH]'
                                  'or ON_AUTH file')
            sys.exit(1)

	if not self.on_rpcxml_endpoint:
            print >> sys.stderr, ('You must provide an OpenNebula RPC-XML endpoint'
                                  'via either --on-rpcxml-endpoint or '
                                  'env[ON_RPCXML_ENDPOINT] ')
            sys.exit(1)

        self.static = providers.static.StaticProvider(opts)

#    def get_compute_endpoints(self):
#        ret = {
#            'endpoints': {},
#            'compute_middleware_developer': 'OpenStack',
#            'compute_middleware': 'OpenStack Nova',
#        }
#
#        defaults = self.static.get_compute_endpoint_defaults(prefix=True)
#        catalog = self.api.client.service_catalog.catalog
#        endpoints = catalog['access']['serviceCatalog']
#        for endpoint in endpoints:
#            if endpoint['type'] == 'occi' :
#                e_type = 'OCCI'
#                e_version = defaults.get('endpoint_occi_api_version', '1.1')
#            elif endpoint['type'] == 'compute':
#                e_type = 'OpenStack'
#                e_version = defaults.get('endpoint_openstack_api_version', '2')
#            else:
#                continue
#
#            for ept in endpoint['endpoints']:
#                e_id = ept['id']
#                e_url = ept['publicURL']
#
#                e = defaults.copy()
#                e.update({'endpoint_url': e_url,
#                          'compute_api_type': e_type,
#                          'compute_api_version': e_version})
#
#                ret['endpoints'][e_id] = e
#
#        return ret

#    There are no flavours into OpenNebula. If you are using rOCCI server (which defines flavours internally), then
#    use the OpenNebulaROCCI driver
#    def get_templates(self):
#        flavors = {}
#
#        defaults = {"platform": "amd64", "network": "private"}
#        defaults.update(self.static.get_template_defaults(prefix=True))
#
#	flavorslist
#	exit
#        for flavor in self.api.flavors.list(detailed=True):
#            if not flavor.is_public:
#                continue
#
#            aux = defaults.copy()
#            aux.update({'template_id': 'resource#%s' % flavor.name,
#                        'template_memory': flavor.ram,
#                        'template_cpu': flavor.vcpus})
#            flavors[flavor.id] = aux
#        return flavors

    def get_images(self):
        images = {}

        template = {
            'image_name': None,
            'image_description': None,
            'image_version': None,
            'image_marketplace_id': None,
            'image_id': None,
            'image_os_family': None,
            'image_os_name': None,
            'image_os_version': None,
            'image_platform': "amd64",
        }
        defaults = self.static.get_image_defaults(prefix=True)
	imgsch='os_tpl'
	if 'image_schema' in defaults:
	    imgsch=defaults['image_schema']

        #Perform request for data
	requestdata='<?xml version="1.0" encoding="UTF-8"?>\n<methodCall>\n<methodName>one.imagepool.info</methodName>\n<params>\n<param><value><string>'+self.on_auth+'</string></value></param>\n<param><value><i4>-2</i4></value></param>\n<param><value><i4>-1</i4></value></param>\n<param><value><i4>-1</i4></value></param>\n</params>\n</methodCall>'

	req = urllib2.Request(self.on_rpcxml_endpoint,requestdata)
	response = urllib2.urlopen(req)

	xml=response.read()
	xmldoc = minidom.parseString(xml)
	itemlist = xmldoc.getElementsByTagName('string')

        id=0
        images={}
	for s in itemlist :
	    xmldocimage=minidom.parseString(s.firstChild.nodeValue)
	    itemlistimage = xmldocimage.getElementsByTagName('IMAGE')
	    for i in itemlistimage :
	        aux = template.copy()
                aux.update(defaults)
                aux.update({'image_name': i.getElementsByTagName('NAME')[0].firstChild.nodeValue,
                        'image_id': '%s#%s' % (imgsch, i.getElementsByTagName('NAME')[0].firstChild.nodeValue)
		})
		if  i.getElementsByTagName('DESCRIPTION').length > 0:
                        aux.update({'image_description': i.getElementsByTagName('DESCRIPTION')[0].firstChild.nodeValue})
		tmpel = i.getElementsByTagName('VMCATCHER_EVENT_AD_MPURI')
                if tmpel.length > 0: aux.update({ 'image_marketplace_id': tmpel[0].firstChild.nodeValue })
                images[id] = aux
                id=id+1
        return images

    @staticmethod
    def populate_parser(parser):
        parser.add_argument('--on-auth',
            metavar='<auth>',
            default=env('ON_AUTH'),
            help='Specify authorization information. For core drivers, it shall be <username>:<password>. Defaults to env[ON_USERNAME] or to ONE_OUTH file.')

        parser.add_argument('--on-rpcxml-endpoint',
            metavar='<auth-url>',
            default=env('OS_RPCXML_ENDPOINT'),
            help='Defaults to env[OS_RPCXML_ENDPOINT].')

