# Cloud BDII provider

## Installation

From source:
    pip install -e .

From repository:

## Usage

See the usage information with:

    cloud-bdii-provider --help

To produce a complete LDIF to be used without a site-BDII use:

    cloud-bdii-provider --full-bdii-ldif

The provider will use a YAML file to load static information. By default it will
look for `etc/bdii.yaml` but this path can be overwriten with:

    cloud-bdii-provider --yaml-file /path/to/yaml/file.yaml

To specify a middleware provider instead of the static provider use
the following (only OpenStack is supported so far).

    cloud-bdii-provider --middleware OpenStack

The provider will use static information if no dynamic values are present or if a
dynamic provider is not able to return information.

### Using the static provider

The static provider will read values from a YAML file and will generate a LDIF
according to those values. See `etc/sample.static.yaml` for a commented sample.

### Using the OpenStack provider

The OpenStack provider will get dynamic information for the templates (flavors),
images and endpoints. However, some static information is still needed, so you will
have to create a YAML file. A sample of a YAML file for OpenStack can be found
in the `etc/sample.openstack.yaml` file.

This provider is not (yet) able to get information from Swift, so this has to be
included by hand.

Once you've generated your YAML file you can run the provider as follows:

    cloud-bdii-reporter  --middleware OpenStack \
        --os-username <username> --os-password <password> \
        --os-tenant-name <tenant> --os-auth-url <auth-url>
