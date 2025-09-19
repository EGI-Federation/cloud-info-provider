# Cloud Information provider

[![Python tests](https://github.com/EGI-Federation/cloud-info-provider/actions/workflows/python.yml/badge.svg)](https://github.com/EGI-Federation/cloud-info-provider/actions/workflows/python.yml/)
[![GitHub release](https://img.shields.io/github/release/EGI-Federation/cloud-info-provider.svg)](https://github.com/EGI-Federation/cloud-info-provider/releases)

The Cloud Information provider generates a representation of cloud resources
following the GlueSchema representation.

The provider extracts information from a cloud deployment using public APIs and
formats as a JSON.

Currently supported cloud middleware:

- OpenStack

## Installation

Use pip:

```sh
pip install cloud-info-provider
```

### From source

Source-based installation is not recommended for production usage, but it is
handy for testing or development purpose. Get the source by cloning this
repository and run with `uv`

```sh
uv run cloud-info-provider-service
```

## Usage

```shell
cloud-info-provider-service <openstack authentication options> <site_config>
```

### Site configuration

The cloud-info-provider uses a YAML file describe the basic information of the
cloud site to represent. This file follows the specification in the
[fedcloud-catchall-operations](https://github.com/EGI-Federation/fedcloud-catchall-operations/tree/main)
for site descriptions:

```yaml
---
gocdb: "<NAME OF THE SITE IN GOCDB>"
endpoint: "https://example.com:5000/v3"
# the images is ignored by the cloud-info-provider
images:
vos:
  - name: "<VO name>"
    auth:
      project_id: "<project id for the VO>"
  - name: ...
```

### Middleware

Dynamic information is obtained with the middleware providers. Use the
`--middleware` option for specifying the provider to use (see the command help
for exact names).

Each dynamic provider has its own command-line options for specifying how to
connect to the underlying service. Use the `--help` option for a complete
listing of options.

#### OpenStack

The `openstack` provider require a working keystone endpoint and valid
credentials to access that endpoint. It uses
[keystoneauth](https://docs.openstack.org/keystoneauth/latest/) so any Keystone
authentication method available in that library can be used. The configured user
for authentication must be a member of every project configured in your shares.
Authentication options largely depend on the authentication method used, default
is username/password. For example, using OpenID Connect against a EGI Check-in
integrated endpoint:

```sh
cloud-info-provider-service --middleware openstack \
    --os-auth-type v3oidcaccesstoken \
    --os-identity-provider egi.eu --os-protocol oidc \
    --os-access-token $ACCESS_TOKEN \
    --os-auth-url https://<keystone-endpoint>:5000/v3
```

Other extra options for the providers (defaults should be OK):

- `--select-flavors {all,public,private}` Select all (`default`), `public` or
  `private` flavors. For more details see
  [OpenStack flavors documentation](https://docs.openstack.org/nova/pike/admin/flavors.html).

- `--all-images` If set, include information about all images (including
  snapshots), otherwise only publish images with EGI registry metadata, ignoring
  the others.

##### Support for specialized hardware (GPU & InfiniBand) through OpenStack properties

The `openstack` provider is able to gather additional GPU and InfiniBand
information made available through flavor's and image's metadata. To this end,
this provider allows passing CLI options (`--property-*`) to match the metadata
keys. As an example, the option `--property-flavor-gpu-vendor gpu:vendor` will
seek for `gpu-vendor` key in the flavor definition (properties field), while
`--property-image-gpu-driver gpu:driver:version` will fetch the value associated
with the `gpu:driver:version` key in the list of images obtained.

For the InfiniBand case, there is an additional option
(`--property-flavor-infiniband-value`) that also checks the value obtained from
the metadata. Only if they match, InfiniBand is considered as supported.

Use the `--help` option for the whole list of available GPU and InfiniBand
properties.

#### CAs

The provider will use your python default CAs for checking and connecting to
your endpoints and GOCDB, so please make sure those CAs include the IGTF CAs.
The location of the CAs depending on how you installed the different python
packages (using deb/rpm packages or `pip`).

For debian-based systems (e.g. Ubuntu), use the following:

```sh
cd /usr/local/share/ca-certificates
for f in /etc/grid-security/certificates/*.pem ; do ln -s $f $(basename $f .pem).crt; done
update-ca-certificates
```

For RH-based systems (e.g. CentOS), you can include the IGTF CAs with:

```sh
cd /etc/pki/ca-trust/source/anchors
ln -s /etc/grid-security/certificates/*.pem .
update-ca-trust extract
```

Otherwise, you need to add the IGTF CAs to the internal requests bundle:

```sh
cat /etc/grid-security/certificates/*.pem >> $(python -m requests.certs)
```

## Creating releases

1. Open an issue to track the release process
1. Create a PR to update the changelog to reflect the changes since last version
   and any other needed changes for the release
   - Version should follow [SemVer](https://semver.org/) like 0.42.0
1. Tag the PR as `release`, this will automate the process of creating the
   release in GitHub and pushing packages to repositories (PyPi) once merged.

## Acknowledgement

This work recieved funding from the [EOSC-hub project](http://eosc-hub.eu/)
(Horizon 2020) under Grant number 777536.
