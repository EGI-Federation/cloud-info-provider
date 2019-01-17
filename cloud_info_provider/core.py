import argparse
import logging

from stevedore import driver
from stevedore import extension


def get_providers():
    def _handle_exception(*args):
        mgr, entry_point, exception = args
        logging.getLogger('stevedore.extension').error((
            "Cannot load '%s': %s") % (entry_point, exception))

    mgr = extension.ExtensionManager(
        namespace='cip.providers',
        on_load_failure_callback=_handle_exception,
        propagate_map_exceptions=True,
    )
    return dict((x.name, x.plugin) for x in mgr)


def get_formatters():
    mgr = extension.ExtensionManager(
        namespace='cip.formatters',
    )
    return [x.name for x in mgr]


def parse_opts(providers, formatters):
    parser = argparse.ArgumentParser(
        description='Cloud BDII provider',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        fromfile_prefix_chars='@',
        conflict_handler="resolve",
    )

    parser.add_argument(
        '--yaml-file',
        default='/etc/cloud-info-provider/static.yaml',
        help=('Path to the YAML file containing configuration static values. '
              'This file will be used to populate the information '
              'to the static provider. These values will be used whenever '
              'a dynamic provider is used and it is not able to produce any '
              'of the required values, or when using the static provider. '))

    parser.add_argument(
        '--template-dir',
        default='/etc/cloud-info-provider/templates',
        help=('Path to the directory containing the needed templates'))

    parser.add_argument(
        'format',
        nargs='?',
        default='glue',
        choices=formatters,
        help=('Selects the output format'))

    parser.add_argument(
        '--site-in-suffix',
        action='store_true',
        default=False,
        help=('Whether to include the site name in the generated DN\'s'
              'suffix (Use only for execution as a site-BDII provider)'))

    parser.add_argument(
        '--middleware',
        metavar='MIDDLEWARE',
        choices=providers,
        default='static',
        help=('Middleware used. Only the following middlewares are '
              'supported: %s. If you do not specify anything, static '
              'values will be used.' % providers.keys()))

    for provider_name, provider in providers.items():
        group = parser.add_argument_group('%s provider options' %
                                          provider_name)
        provider.populate_parser(group)

    return parser.parse_args()


def main():
    providers = get_providers()
    formatters = get_formatters()

    opts = parse_opts(providers, formatters)

    mgr = driver.DriverManager(
        namespace='cip.formatters',
        name=opts.format,
        invoke_on_load=True,
    )
    mgr.driver.format(opts, providers)


if __name__ == '__main__':
    main()
