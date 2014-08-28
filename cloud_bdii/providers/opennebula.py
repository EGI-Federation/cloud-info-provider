# This provider is for an OpenNebula middleware. Part of the information is
# retreived from OpenNebula, the rest is provided via the static template. Note
# that this is a generic OpenNebula plugin. If you use rOCCI server on top of
# OpenNebula, please refer to the OpenNebulaROCCI provider

import argparse
import sys
import urllib2
import xml.etree.ElementTree as xee

from cloud_bdii import providers
from cloud_bdii import utils


class OpenNebulaBaseProvider(providers.BaseProvider):
    def __init__(self, opts):
        super(OpenNebulaBaseProvider, self).__init__(opts)

        self.on_auth = opts.on_auth
        self.on_rpcxml_endpoint = opts.on_rpcxml_endpoint

        if self.on_auth is None:
            print >> sys.stderr, ('ERROR, You must provide a on_auth '
                                  'via either --on-auth or env[ON_AUTH]'
                                  'or ON_AUTH file')
            sys.exit(1)

        if not self.on_rpcxml_endpoint:
            print >> sys.stderr, ('You must provide an OpenNebula RPC-XML '
                                  'endpoint via either --on-rpcxml-endpoint or'
                                  ' env[ON_RPCXML_ENDPOINT] ')
            sys.exit(1)
        self.static = providers.static.StaticProvider(opts)

    def _get_from_xml(self, what):
        # FIXME(aloga): exception on bad what
        requestdata = ("<?xml version='1.0' encoding='UTF-8'?>"
                       "<methodCall>"
                       "<methodName>%s</methodName>"
                       "<params>"
                       "<param><value><string>'%s'</string></value></param>"
                       "<param><value><i4>-2</i4></value></param>"
                       "<param><value><i4>-1</i4></value></param>"
                       "<param><value><i4>-1</i4></value></param>"
                       "</params>"
                       "</methodCall>" % (what, self.on_auth))

        req = urllib2.Request(self.on_rpcxml_endpoint, requestdata)
        response = urllib2.urlopen(req)

        xml = response.read()
        # NOTE(aloga): this is wrong in so may ways, but it is more or less the
        # same that was before. Leave it like that, thenrefactor it
        doc = xee.fromstring(xml)
        doc = xee.fromstring(doc.find("params/param/value/string").text)
        templates = doc.getchildren()

        def _recurse_dict(element):
            return (element.tag.lower(),
                    dict(map(_recurse_dict, element)) or element.text)

        return [_recurse_dict(e) for e in templates]

    @staticmethod
    def _gen_id(image_name, image_id, schema):
        # FIXME(aloga): make this an abstrac method
        """Generate image id."""
        return '%s#%s' % (schema, image_id)

    def _get_one_images(self):
        return dict([(img["name"], img) for _, img in self._get_from_xml(
            "one.imagepool.info")])

    def _get_one_templates(self):
        return dict([(tpl["id"], tpl) for _, tpl in self._get_from_xml(
            "one.templatepool.info")])

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
            aux_tpl["image_description"] = tpl.get("description", None)
            disk = tpl.get("template", {}).get("disk", {}).get("image", None)
            if disk is not None:
                aux = one_images.get(disk, {}).get("template", {})
                aux_tpl["image_marketplace_id"] = aux.get(
                    "vmcatcher_event_ad_mpuri", None
                )
            templates[tpl_id] = aux_tpl
        return templates

    @staticmethod
    def populate_parser(parser):
        # FIXME(aloga): we should use groups so that this
        # try ... except is not needed
        try:
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
        except argparse.ArgumentError:
            pass


class OpenNebulaProvider(OpenNebulaBaseProvider):
    def __init__(self, opts):
        super(OpenNebulaProvider, self).__init__(opts)
