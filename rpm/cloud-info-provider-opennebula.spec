#
# cloud-info-provider-opennebula RPM
#

Summary: Cloud Information provider meta-package for OpenNebula
Name: cloud-info-provider-opennebula
Version: 0.9.1
Release: 1%{?dist}
Group: Applications/Internet
# License: ASL 2.0
# License: MIT
License: DWTF
URL: https://github.com/EGI-Foundation/cloud-info-provider
# XXX Check if source is really needed for meta-package
# Source: cloud_info_provider-%{version}.tar.gz

Requires: cloud-info-provider
# OpenNebula-specific dependencies
Requires: python-defusedxml
BuildArch: noarch

%description
OpenNebula-specific meta-package for Information provider for Cloud Compute and
Cloud Storage services.
Install the cloud-information-provider and the Cloud Middleware dependencies.

# XXX Check if all sections should be present
%prep

%build

%install

%clean

%files

%changelog
* Wed Jun 20 2018 Baptiste Grenier <baptiste.grenier@egi.eu> 0.9.1
- First release, numbering align to cloud-info-provider package (Baptiste Grenier)
