# This provider is for an OpenNebula middleware. Part of the information is
# retreived from OpenNebula, the rest is provided via the static template. Note
# that this is a generic OpenNebula plugin. If you use rOCCI server on top of
# OpenNebula, please refer to the OpenNebulaROCCI provider

import json
import os
import string
import xml.etree.ElementTree as xee

from six.moves import urllib

from cloud_info import exceptions
from cloud_info import providers
from cloud_info import utils


class OpenNebulaBaseProvider(providers.BaseProvider):
    def __init__(self, opts):
        super(OpenNebulaBaseProvider, self).__init__(opts)

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
        requestdata = ("<?xml version='1.0' encoding='UTF-8'?>"
                       "<methodCall>"
                       "<methodName>%s</methodName>"
                       "<params>"
                       "<param><value><string>%s</string></value></param>"
                       "<param><value><i4>-2</i4></value></param>"
                       "<param><value><i4>-1</i4></value></param>"
                       "<param><value><i4>-1</i4></value></param>"
                       "</params>"
                       "</methodCall>" % (what, self.on_auth))

        req = urllib.request.Request(self.on_rpcxml_endpoint, requestdata)
        response = urllib.request.urlopen(req)

        xml = response.read()
        # NOTE(aloga): this is wrong in so may ways, but it is more or less the
        # same that was before. Leave it like that, thenrefactor it
        doc = xee.fromstring(xml)
        doc = doc.find("params/param/value/array/data/value/string").text
        doc = xee.fromstring(doc.encode('utf-8'))
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
        for tpl_id, tpl in one_templates.items():
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


class OpenNebulaProvider(OpenNebulaBaseProvider):
    def __init__(self, opts):
        super(OpenNebulaProvider, self).__init__(opts)


class IndigoONProvider(OpenNebulaBaseProvider):
    def __init__(self, opts):
        super(IndigoONProvider, self).__init__(opts)

    def get_templates(self):
        template = {
            'template_id': None,
            'template_name': None,
            'template_description': None,
            'template_memory': None,
            'template_cpu': None,
            'template_platform': 'amd64',
            'network': 'private',
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
        # TODO(document)
        for tpl_id, tpl in one_templates.items():
            aux_tpl = template.copy()
            aux_tpl.update(defaults)
            if "template" in tpl:
                tpl_tpl = tpl["template"]
                if "description" in tpl_tpl:
                    aux_tpl["template_description"] = tpl_tpl["description"]
                if "cpu" in tpl_tpl:
                    aux_tpl["template_cpu"] = tpl_tpl["cpu"]
                if "memory" in tpl_tpl:
                    aux_tpl["template_memory"] = tpl_tpl["memory"]
            aux_tpl["template_id"] = self._gen_id(tpl["name"],
                                                  tpl_id, img_schema)
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

    def get_images(self):
        defaults = self.static.get_image_defaults(prefix=True)

        images = {}
        # XXX need to call this or tests will fail
        # as templates will be returned instead of images
        self._get_one_templates()
        one_images = self._get_one_images()

        # add all the custom fields
        for img_name, img in one_images.items():
            aux_img = {}
            aux_img.update(defaults)
            aux_img["image_name"] = img_name
            img_id = img["id"]
            aux_img["image_id"] = img_id

            # XXX could probably be move to the mako template
            image_descr = None

            if "template" in img:
                aux = img["template"]
                for name, value in aux.items():
                    aux_img[name] = value
                aux_img["image_marketplace_id"] = aux.get(
                    "vmcatcher_event_ad_mpuri", None)
                if aux.get('vmcatcher_event_dc_description', None) is not None:
                    image_descr = aux['vmcatcher_event_dc_description']
                elif "description" in aux:
                    image_descr = aux.get("description")
                elif 'vmcatcher_event_dc_title' in aux:
                    image_descr = aux['vmcatcher_event_dc_title']

            if (self.opts.vmcatcher_images and
                    aux_img.get("image_marketplace_id", None) is None):
                continue
            if image_descr:
                aux_img['image_description'] = image_descr
            images[img_id] = aux_img
        return images


class OpenNebulaROCCIProvider(OpenNebulaBaseProvider):
    def __init__(self, opts):
        super(OpenNebulaROCCIProvider, self).__init__(opts)

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

            mxn = jd['mixins'][0]

            aux = defaults.copy()
            if ressch is None:
                flid = '%s#%s' % (mxn['scheme'].rstrip('#'), mxn['term'])
            else:
                flid = '%s#%s' % (ressch, mxn['term'])
                aux.update({'template_id': '%s#%s' % (ressch, mxn['term'])})

            occi_attrs = mxn['attributes']['occi']['compute']
            if 'ephemeral_storage' in occi_attrs:
                disk = occi_attrs['ephemeral_storage']['size']['Default']
            else:
                disk = 0

            aux.update({
                'template_id': flid,
                'template_cpu': occi_attrs['cores']['Default'],
                'template_memory': int(occi_attrs['memory']['Default'] * 1024),
                'template_description': mxn['title'],
                'template_disk': disk,
            })

            flavors[flid] = aux
        return flavors

    @staticmethod
    def populate_parser(parser):
        super(OpenNebulaROCCIProvider,
              OpenNebulaROCCIProvider).populate_parser(parser)

        parser.add_argument(
            '--rocci-template-dir',
            metavar='<rocci-template-dir>',
            default=None,
            help='Location of the rOCCI-server template definitions.')

    @staticmethod
    def _gen_id(image_name, image_id, schema):
        """Generate image uiid as rOCCI does."""
        replace_punctuation = utils.maketrans(
            string.punctuation + string.whitespace,
            '_' * len(string.punctuation + string.whitespace)
        )
        image_name = utils.translate(image_name.lower(),
                                     replace_punctuation).strip('_')
        return '%s#uuid_%s_%s' % (schema, image_name, image_id)
