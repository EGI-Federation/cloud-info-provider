# Cloud BDII provider

## Installation

    pip install -e .

## Usage

See the usage information with:

    cloud-bdii-provider --help

To produce a complete LDIF to be used without a site-BDII use:

    cloud-bdii-provider --full-bdii-ldif

To specify a middleware provider instead of the static provider use
the following (only OpenStack is supported so far):

    cloud-bdii-provider --middleware OpenStack

### Using the static provider

The static provider will read values from a YAML file and will generate a LDIF
according to those values. See `etc/static_sample.yaml` for a sample. Once
you've generated your YAML file you should specify it as follows:

    cloud-bdii-provider --yaml-file /path/to/yaml/file.yaml

### Using the OpenStack provider

TBD
