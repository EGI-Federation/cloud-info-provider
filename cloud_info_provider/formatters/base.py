import abc
import logging
import os

import mako.exceptions
import mako.template
import six
from stevedore import extension


@six.add_metaclass(abc.ABCMeta)
class BaseFormatter(object):
    """Base class for the formatters."""

    def __init__(self):
        self.template_extension = ""
        self.templates = []
        self.templates_files = {}

    def _load_collectors(self, opts, providers, auth_refresher):
        mgr = extension.ExtensionManager(
            namespace="cip.collectors",
            invoke_on_load=True,
            invoke_args=(opts, providers, auth_refresher),
        )
        return dict((x.name, x.obj) for x in mgr)

    def _load_templates(self, template_dir):
        self.templates_files = {}
        if not template_dir:
            template_dir = os.path.join(os.path.dirname(__file__), "templates")
        for tpl in self.templates:
            template_file = os.path.join(
                template_dir, "%s.%s" % (tpl, self.template_extension)
            )
            self.templates_files[tpl] = template_file

    def _format_template(self, template, info, extra={}):
        info = info.copy()
        info.update(extra)
        t = self.templates_files[template]
        tpl = mako.template.Template(filename=t)
        try:
            return tpl.render(attributes=info)
        except Exception:
            logging.error(mako.exceptions.text_error_template().render())
            raise

    def format(self, opts, providers, auth_refreshers):
        output = []
        available_collectors = self._load_collectors(opts, providers, auth_refreshers)
        self._load_templates(opts.template_dir)
        for tpl in self.templates:
            info = available_collectors[tpl].fetch()
            if info:
                output.append(self._format_template(tpl, info))
        return "\n".join(output)
