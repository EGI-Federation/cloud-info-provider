import abc
import os
import six

import mako.exceptions
import mako.template


@six.add_metaclass(abc.ABCMeta)
class BaseFormatter(object):
    """Base class for the formatters."""
    def __init__(self):
        self.template_extension = None
        self.templates = []
        self.cls = []
        self.templates_files = {}

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
        self._load_templates(opts.template_dir)
        for cls_ in self.cls:
            c = cls_(opts)
            info = c.load()
            if info:
                for tpl in c.templates:
                    if tpl in self.templates:
                        print(self._format_template(tpl, info).encode('utf-8'))
