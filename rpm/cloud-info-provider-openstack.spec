#
# cloud-info-provider-openstack RPM
#

Summary: Cloud Information provider meta-package for OpenStack
Name: cloud-info-provider-deep-openstack
Version: %{_pbr_version}
Release: 1%{?dist}
Group: Applications/Internet
License: Apache Software License 2.0
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
=======
=======
* Mon Mar 04 2019 Baptiste Grenier <baptiste.grenier@egi.eu> 0.11.3
- Fix handling of network info (#151). (Baptiste Grenier)
* Thu Jan 31 2019 Enol Fernández <enol.fernandez@egi.eu> 0.11.2
- Version bump (Enol Fernandez)
* Tue Jan 29 2019 Baptiste Grenier <baptiste.grenier@egi.eu> 0.11.1
- Version bump (Baptiste Grenier)
* Sun Jan 27 2019 Baptiste Grenier <baptiste.grenier@egi.eu> 0.11.0
- Split OpenStack and OOI providers. (Enol Fernandez)
- Review and update output to implement latest GLUE2.1 updates. (Enol Fernandez, Baptiste Grenier)
* Wed Jan 09 2019 Enol Fernández <enol.fernandez@egi.eu> 0.10.3
- Updated dependencies
* Thu Nov 8 2018 Pablo Orviz <orviz@ifca.unican.es> 0.10.4
- Add support for Infiniband in OpenStack (Pablo Orviz)
* Mon Oct 15 2018 Baptiste Grenier <baptiste.grenier@egi.eu> 0.10.2
- Version bump (Baptiste Grenier)
* Mon Oct 01 2018 Baptiste Grenier <baptiste.grenier@egi.eu> 0.10.0
- Version bump (Baptiste Grenier)
* Wed Jun 20 2018 Baptiste Grenier <baptiste.grenier@egi.eu> 0.9.1
- First release, numbering aligned to cloud-info-provider package (Baptiste Grenier)
