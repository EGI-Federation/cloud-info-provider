# This provider is for an OpenNebula middleware. Part of the information is
# retreived from OpenNebula, the rest is provided via the static template. Note
# that this is a generic OpenNebula plugin. If you use rOCCI server on top of
# OpenNebula, please refer to the OpenNebulaROCCI provider

import json
import os
import string
import xml.etree.ElementTree as xee
import xmlrpclib

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

    # Return noenmpty string from xml if exists
    @staticmethod
    def get_xml_string(xml, tag, emptystring):
        search_result = xml.find(tag)
        if search_result is None:
            return None
        if search_result.text == emptystring:
            return None
        return search_result.text

    def get_images(self):
        defaults = self.static.get_image_defaults(prefix=True)
        img_schema = defaults.get('image_schema', 'os_tpl')

        # Mamut
        # Setup server for XMLRPC connector
        serverproxy = xmlrpclib.ServerProxy(self.on_rpcxml_endpoint)

        # Get templates
        response = serverproxy.one.templatepool.info(self.on_auth, -2, -1, -1)

        # In case request fails raise exeption
        if not response[0]:
            raise exceptions.OpenNebulaProviderException(response[1])

        # raise exceptions.OpenNebulaProviderException(response[1])
        # Get XML templatesi
        xml_templates = []
        doc = xee.fromstring(response[1])
        # Create template list with only FEDcloud templates,
        # generated from VMcatcher (must have nifty elements)
        for template_index, xml_template in enumerate(doc.getchildren()):
            # raise exceptions.OpenNebulaProviderException(xml_template)
            if (xml_template.find("TEMPLATE/NIFTY_APPLIANCE_ID") is not None):
                xml_templates.append(xml_template)

        # Form template list
        templates = {}
        for template_index, xml_template in enumerate(xml_templates):
            tmp_template = {
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
            # image_name
            tmp_template["image_name"] = self.get_xml_string(
                xml_template, "NAME", '""""')

            # image_id
            name = self.get_xml_string(xml_template, "NAME", '""""')
            ident = self.get_xml_string(xml_template, "ID", '""""')
            if (name is not None) and (ident is not None):
                tmp_template["image_id"] = self._gen_id(
                    tmp_template["image_name"], ident, img_schema)

            # image_version
            tmp_template["image_version"] = self.get_xml_string(
                xml_template, "TEMPLATE/VMCATCHER_EVENT_HV_VERSION", '""""')

            # image_description with fallback
            tmp_template["image_description"] = self.get_xml_string(
                xml_template, "TEMPLATE/NIFTY_APPLIANCE_DESCRIPTION", '""""')
            if tmp_template["image_description"] is None:
                tmp_template["image_description"] = self.get_xml_string(
                    xml_template, "TEMPLATE/VMCATCHER_EVENT_DC_DESCRIPTION",
                    '""""')
            if tmp_template["image_description"] is None:
                tmp_template["image_description"] = self.get_xml_string(
                    xml_template, "DESCRIPTION", '""""')

            templates[template_index] = tmp_template
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
            '--rocci-template-dir',
            metavar='<rocci-template-dir>',
            default=None,
            help='Location of the rOCCI-server template definitions.')
