import argparse
import logging

import cloud_info_provider
from stevedore import driver, extension


def get_providers():
    def _handle_exception(*args):
        mgr, entry_point, exception = args
        logging.getLogger("stevedore.extension").error(
            ("Cannot load '%s': %s") % (entry_point, exception)
        )

    mgr = extension.ExtensionManager(
        namespace="cip.providers",
        on_load_failure_callback=_handle_exception,
        propagate_map_exceptions=True,
    )
    return dict((x.name, x.plugin) for x in mgr)


def get_formatters():
    mgr = extension.ExtensionManager(
        namespace="cip.formatters",
    )
    return [x.name for x in mgr]


def get_publishers():
    mgr = extension.ExtensionManager(
        namespace="cip.publishers",
    )
    return dict((x.name, x.plugin) for x in mgr)


def get_parser(providers, formatters, publishers):
    parser = argparse.ArgumentParser(
        description="Cloud Information System provider",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        fromfile_prefix_chars="@",
        conflict_handler="resolve",
    )

    parser.add_argument(
        "--version", action="version", version=f"{cloud_info_provider.__version__}"
    )

    parser.add_argument(
        "--middleware",
        metavar="MIDDLEWARE",
        choices=providers,
        default="openstack",
        help=(
            "Middleware used. Only the following middlewares are "
            "supported: {%(choices)s}"
        ),
    )

    parser.add_argument(
        "--format",
        metavar="FORMAT",
        choices=formatters,
        default="glue21json",
        help=("Selects the output format. Allowed values: {%(choices)s}"),
    )

    parser.add_argument(
        "--publisher",
        metavar="PUBLISHER",
        choices=publishers,
        default="stdout",
        help=("Selects where to publish output to. Allowed values: " "%(choices)s}"),
    )

    parser.add_argument(
        "--timeout",
        default=600,
        metavar="<seconds>",
        help="Set request timeout (in seconds).",
    )

    parser.add_argument(
        "--insecure",
        action="store_true",
        help="Explicitly allow to perform 'insecure' "
        "SSL (https) requests. The server's certificate will "
        "not be verified against any certificate authorities. "
        "This option should be used with caution.",
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        default=False,
        help="Provide extra logging information",
    )

    parser.add_argument(
        "--exit-on-share-errors",
        action="store_true",
        default=False,
        help=("Exit if there are errors getting information from a share."),
    )

    for provider_name, provider in providers.items():
        group = parser.add_argument_group("%s provider options" % provider_name)
        provider.populate_parser(group)

    for publisher_name, publisher in publishers.items():
        group = parser.add_argument_group("%s publisher options" % publisher_name)
        publisher.populate_parser(group)

    return parser


def main():
    providers = get_providers()
    formatters = get_formatters()
    publishers = get_publishers()

    opts = get_parser(providers, formatters, publishers).parse_args()

    formatter = driver.DriverManager(
        namespace="cip.formatters",
        name=opts.format,
        invoke_on_load=True,
    )

    publisher = driver.DriverManager(
        namespace="cip.publishers",
        name=opts.publisher,
        invoke_on_load=True,
        invoke_args=(opts,),
    )

    provider_class = providers.get(opts.middleware)
    glue = provider_class(opts).fetch()

    output = formatter.driver.format(opts, glue)
    publisher.driver.publish(output)


if __name__ == "__main__":
    main()
