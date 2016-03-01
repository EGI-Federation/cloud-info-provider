# This provider is for an OpenNebula middleware. Part of the information is
# retreived from OpenNebula, the rest is provided via the static template. Note
# that this is a generic OpenNebula plugin. If you use rOCCI server on top of
# OpenNebula, please refer to the OpenNebulaROCCI provider

import json
import os
import string
import xmlrpclib
import xml.etree.ElementTree as xee

from cloud_bdii import exceptions
from cloud_bdii import providers
from cloud_bdii import utils


class OpenNebulaProvider(providers.BaseProvider):
    def __init__(self, opts):
	super(OpenNebulaProvider, self).__init__(opts)

        self.on_auth = opts.on_auth
        self.on_rpcxml_endpoint = opts.on_rpcxml_endpoint

        if self.on_auth is None:
            msg = ('ERROR, You must provide a on_auth '
                   'via either --on-auth or env[ON_AUTH]'
                   'or ON_AUTH file')
            raise exceptions.OpenNebulaProviderException(msg)

        if not self.on_rpcxml_endpoint:
            msg = ('You must provide an OpenNebula RPC-XML '
                   'endpoint via either --on-rpcxml-endpoint or'
                   ' env[ON_RPCXML_ENDPOINT] ')
            raise exceptions.OpenNebulaProviderException(msg)

        self.opts = opts
        self.static = providers.static.StaticProvider(opts)

    def _get_from_xml(self, what):
        # FIXME(aloga): exception on bad what
	#Connect to XMLRPC server and invoke selected method
	serverproxy = xmlrpclib.ServerProxy("https://carach5.ics.muni.cz:6443/RPC2")
	xmlrpccall = getattr(serverproxy, what)	
	response = xmlrpccall(str(self.on_auth),-2,-1,-1)
		
	#In case request fails raise exeption
	if not response[0]:
	    raise exceptions.OpenNebulaProviderException(response[1])
	
      	#Parse obtained XML
	doc = xee.fromstring(response[1])
        templates = doc.getchildren()

        def _recurse_dict(element):
            return (element.tag.lower(),
                    dict(map(_recurse_dict, element)) or element.text)

        return [_recurse_dict(e) for e in templates]

    @staticmethod
    def _gen_id(image_name, image_id, schema):
        """Generate image uiid as rOCCI does."""
        replace_punctuation = string.maketrans(
            string.punctuation + string.whitespace,
            '_' * len(string.punctuation + string.whitespace)
        )
        image_name = string.translate(image_name.lower(),
                                      replace_punctuation).strip('_')
        return '%s#uuid_%s_%s' % (schema, image_name, image_id)

    def _get_one_images(self):
        return dict([(img["name"], img) for _, img in self._get_from_xml(
            "one.imagepool.info")])

    def _get_one_templates(self):
        return dict([(tpl["id"], tpl) for _, tpl in self._get_from_xml(
            "one.templatepool.info")])

    # The flavours are retreived directly from rOCCI-server configuration
    # files. If the script has no access to them, you can set the directory to
    # None and configuration files specified in the YAML configuration.
    def get_templates(self):
        """Get flavors from rOCCI-server configuration."""

        if self.opts.rocci_template_dir is None:
            # revert to static
            return self.static.get_templates()

        defaults = {'platform': 'amd64', 'network': 'private'}
        defaults.update(self.static.get_template_defaults(prefix=True))
        ressch = defaults.get('template_schema', None)

        # Try to parse template dir
        try:
            template_files = os.listdir(self.opts.rocci_template_dir)
        except OSError as e:
            raise e

        flavors = {}
        for template_file in template_files:
            template_file = os.path.join(self.opts.rocci_template_dir,
                                         template_file)
            with open(template_file, 'r') as fd:
                jd = json.load(fd)

            aux = defaults.copy()
            if ressch is None:
                flid = '%s#%s' % (jd['mixins'][0]['scheme'].rstrip('#'), jd['mixins'][0]['term'])  # noqa
            else:
                flid = '%s#%s' % (ressch, jd['mixins'][0]['term'])
                aux.update({'template_id': '%s#%s' % (ressch, jd['mixins'][0]['term'])})  # noqa

            aux.update({
                'template_id': flid,
                'template_cpu': jd['mixins'][0]['attributes']['occi']['compute']['cores']['Default'],  # noqa
                'template_memory': int(jd['mixins'][0]['attributes']['occi']['compute']['memory']['Default'] * 1024),  # noqa
                'template_description': jd['mixins'][0]['title']
            })

            flavors[flid] = aux
        return flavors

    def get_images(self):
        template = {
            'image_name': None,
            'image_description': None,
            'image_version': None,
            'image_marketplace_id': None,
            'image_id': None,
            'image_os_family': None,
            'image_os_name': None,
            'image_os_version': None,
            'image_platform': 'amd64',
        }
        defaults = self.static.get_image_defaults(prefix=True)
        img_schema = defaults.get('image_schema', 'os_tpl')

        templates = {}
        one_templates = self._get_one_templates()
        one_images = self._get_one_images()

        # 1. take a VMTEMPLATE from templatepool
        # 2. use metadata from VMTEMPLATE to create an os_tpl mixin
        # 3. take the first disk from VMTEMPLATE
        # 4. use disk's IMAGE element to find it in the imagepool
        # 5. associate selected IMAGE metadata (*VMCATCHER* stuff) with the tpl
        for tpl_id, tpl in one_templates.iteritems():
            aux_tpl = template.copy()
            aux_tpl.update(defaults)
            aux_tpl["image_name"] = tpl["name"]
            aux_tpl["image_id"] = self._gen_id(tpl["name"], tpl_id, img_schema)
            disk = tpl.get("template", {}).get("disk", {}).get("image", None)
            if disk is not None:
                aux = one_images.get(disk, {}).get("template", {})
                aux_tpl["image_marketplace_id"] = aux.get(
                    "vmcatcher_event_ad_mpuri", None
                )
                aux_tpl["image_description"] = aux.get("description", None)
                aux_tpl["image_version"] = aux.get(
                    "vmcatcher_event_hv_version",
                    None
                )
            if (self.opts.vmcatcher_images and
                    aux_tpl.get("image_marketplace_id", None) is None):
                continue
            templates[tpl_id] = aux_tpl
        return templates

    @staticmethod
    def populate_parser(parser):
        parser.add_argument(
            '--on-auth',
            metavar='<auth>',
            default=utils.env('ON_AUTH'),
            help=('Specify authorization information. For core drivers, '
                    'it shall be <username>:<password>. '
                    'Defaults to env[ON_USERNAME].'))

        parser.add_argument(
            '--on-rpcxml-endpoint',
            metavar='<auth-url>',
            default=utils.env('OS_RPCXML_ENDPOINT'),
            help='Defaults to env[OS_RPCXML_ENDPOINT].')

        parser.add_argument(
            '--vmcatcher-images',
            action='store_true',
            default=False,
            help=('If set, include only information on images that '
                  'have vmcatcher metadata, ignoring the others.'))

        parser.add_argument(
            '--rocci-template-dir',
            metavar='<rocci-template-dir>',
            default=None,
            help='Location of the rOCCI-server template definitions.')

