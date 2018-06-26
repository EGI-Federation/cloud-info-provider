#
# cloud-info-provider-openstack RPM
#

Summary: Cloud Information provider meta-package for OpenStack
Name: cloud-info-provider-openstack
Version: 0.9.1
Release: 1%{?dist}
Group: Applications/Internet
# License: ASL 2.0
# License: MIT
License: DWTF
URL: https://github.com/EGI-Foundation/cloud-info-provider

Requires: cloud-info-provider
# OpenStack-specific dependencies
Requires: python-novaclient
Requires: python-glanceclient
Requires: python-keystoneauth1
BuildArch: noarch

%description
OpenStack-specific meta-package for Information provider for Cloud Compute and
Cloud Storage services.
Install the cloud-information-provider and the Cloud Middleware dependencies.

%files

%changelog
* Wed Jun 20 2018 Baptiste Grenier <baptiste.grenier@egi.eu> 0.9.1
- First release, numbering aligned to cloud-info-provider package (Baptiste Grenier)
