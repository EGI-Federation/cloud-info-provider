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
        self.template_extension = ''
        self.templates = []
        self.templates_files = {}

    def _load_collectors(self, opts, providers):
        mgr = extension.ExtensionManager(
            namespace='cip.collectors',
            invoke_on_load=True,
            invoke_args=(opts, providers),
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

    def format(self, opts, providers):
        available_collectors = self._load_collectors(opts, providers)
        self._load_templates(opts.template_dir)
        for tpl in self.templates:
            _collector = available_collectors[tpl]
            info = _collector.fetch()
            if info:
                extra_info = {
                    'middleware': opts.middleware,
                    'dynamic_provider': _collector.dynamic_provider}
                print(self._format_template(tpl,
                                            info,
                                            extra_info).encode('utf-8'))
