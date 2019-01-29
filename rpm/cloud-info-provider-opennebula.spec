#
# cloud-info-provider-opennebula RPM
#

Summary: Cloud Information provider meta-package for OpenNebula
Name: cloud-info-provider-opennebula
Version: 0.11.1
Release: 1%{?dist}
Group: Applications/Internet
License: Apache Software License 2.0
URL: https://github.com/EGI-Foundation/cloud-info-provider

Requires: cloud-info-provider
# OpenNebula-specific dependencies
Requires: python-defusedxml
BuildArch: noarch

%description
OpenNebula-specific meta-package for Information provider for Cloud Compute and
Cloud Storage services.
Install the cloud-information-provider and the Cloud Middleware dependencies.

%files

%changelog
* Tue Jan 29 2019 Baptiste Grenier <baptiste.grenier@egi.eu> 0.11.1
- Version bump (Baptiste Grenier)
* Sun Jan 27 2019 Baptiste Grenier <baptiste.grenier@egi.eu> 0.11.0
- Fix os_tpl identifier for OpenNebula with rOCCI. (Boris Parak)
- Review and update output to implement latest GLUE2.1 updates. (Enol Fernandez, Baptiste Grenier)
* Wed Jan 09 2019 Enol Fernández <enol.fernandez@egi.eu> 0.10.3
- Updated dependencies
* Mon Oct 15 2018 Baptiste Grenier <baptiste.grenier@egi.eu> 0.10.2
- Version bump (Baptiste Grenier)
* Mon Oct 01 2018 Baptiste Grenier <baptiste.grenier@egi.eu> 0.10.0
- Version bump (Baptiste Grenier)
* Wed Jun 20 2018 Baptiste Grenier <baptiste.grenier@egi.eu> 0.9.1
- First release, numbering aligned to cloud-info-provider package (Baptiste Grenier)
