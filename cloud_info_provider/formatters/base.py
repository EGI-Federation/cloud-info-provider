import abc
import os
import six

import mako.exceptions
import mako.template

from stevedore import extension


@six.add_metaclass(abc.ABCMeta)
class BaseFormatter(object):
    """Base class for the formatters."""
    def __init__(self):
        self.template_extension = None
        self.templates = []
        self.templates_files = {}

    def _load_fetchers(self, opts):
        mgr = extension.ExtensionManager(
            namespace='cip.fetchers',
            invoke_on_load=True,
            invoke_args=(opts,),
        )
        return dict((x.name, x.obj) for x in mgr)

    def _load_templates(self, template_dir):
        self.templates_files = {}
        for tpl in self.templates:
            template_file = os.path.join(
                template_dir,
                '%s.%s' % (tpl, self.template_extension))
            self.templates_files[tpl] = template_file

    def _format_template(self, template, info, extra={}):
        info = info.copy()
        info.update(extra)
        t = self.templates_files[template]
        tpl = mako.template.Template(filename=t)
        try:
            return tpl.render(attributes=info)
        except Exception:
            return mako.exceptions.text_error_template().render()

    def format(self, opts):
        available_fetchers = self._load_fetchers(opts)
        self._load_templates(opts.template_dir)
        for tpl in self.templates:
            info = available_fetchers[tpl].fetch()
            if info:
                print(self._format_template(tpl, info).encode('utf-8'))
