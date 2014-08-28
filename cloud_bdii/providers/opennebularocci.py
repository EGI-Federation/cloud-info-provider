# This provider is for an OpenNebula middleware using the rOCCI server. Part of
# the information is retreived from OpenNebula, part of it is retreived from
# rOCCI directly. To retreive flavour information, rOCCI

import os
import json
import re

from cloud_bdii.providers import opennebula


class OpenNebulaROCCIProvider(opennebula.OpenNebulaBaseProvider):
    def __init__(self, opts):
        super(OpenNebulaROCCIProvider, self).__init__(opts)

    # The flavours are retreived directly from rOCCI-server configuration
    # files. If the script has no access to them, you can set the directory to
    # None and configuration files specified in the YAML configuration.
    def get_templates(self):

        if (('template_dir' not in self.static.yaml['compute']) or
                (not self.static.yaml['compute']['template_dir']) or
                (self.static.yaml['compute']['template_dir'] is None)):
            # revert to static
            return self.static.get_templates()

        defaults = {'platform': 'amd64', 'network': 'private'}
        defaults.update(self.static.get_template_defaults(prefix=True))
        ressch = defaults.get('template_schema', None)

        # Try to parse template dir
        template_dir = self.static.yaml['compute']['template_dir']
        dlist = os.listdir(template_dir)
        flavors = {}
        flid = 0
        for d in dlist:
            jf = open(template_dir + '/' + d, 'r')
            jd = json.load(jf)
            jf.close()

            aux = defaults.copy()
            if ressch is None:
                aux.update({'template_id': '%s#%s' % (jd['mixins'][0]['scheme'].rstrip('#'), jd['mixins'][0]['term'])})  # noqa
            else:
                aux.update({'template_id': '%s#%s' % (ressch, jd['mixins'][0]['term'])})  # noqa
                aux.update({'template_cpu': jd['mixins'][0]['attributes']['occi']['compute']['cores']['Default'],  # noqa
                            'template_memory': int(jd['mixins'][0]['attributes']['occi']['compute']['memory']['Default'] * 1024),  # noqa
                            'template_description': jd['mixins'][0]['title']})

            flavors[flid] = aux
            flid = flid + 1

        return flavors

    @staticmethod
    def _gen_id(image_name, image_id, schema):
        """Generate image uiid as rOCCI does."""
        # FIXME(aloga): clean this
        tmpimgid = image_name
        tmpimgid = tmpimgid.lower()
        tmpimgid = re.sub(r'(?![a-z0-9]).', '_', tmpimgid)
        tmpimgid = re.sub(r'_+', '_', tmpimgid)
        tmpimgid = tmpimgid.strip('_')
        tmpimgid = '%s#uuid_%s_%s' % (schema, tmpimgid, image_id)  # noqa
        return tmpimgid
