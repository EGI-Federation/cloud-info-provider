#
# cloud-info-provider-openstack RPM
#

Summary: Cloud Information provider meta-package for OpenStack
Name: cloud-info-provider-deep-openstack
Version: %{_pbr_version}
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
* Thu Oct 8 2018 Pablo Orviz <orviz@ifca.unican.es> 0.10.4
- Add support for Infiniband in OpenStack (Pablo Orviz)
* Mon Oct 15 2018 Baptiste Grenier <baptiste.grenier@egi.eu> 0.10.2
- Version bump (Baptiste Grenier)
* Mon Oct 01 2018 Baptiste Grenier <baptiste.grenier@egi.eu> 0.10.0
- Version bump (Baptiste Grenier)
* Wed Jun 20 2018 Baptiste Grenier <baptiste.grenier@egi.eu> 0.9.1
- First release, numbering aligned to cloud-info-provider package (Baptiste Grenier)
