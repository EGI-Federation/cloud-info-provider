#
# cloud-info-provider-openstack RPM
#

Summary: Cloud Information provider meta-package for OpenStack
Name: cloud-info-provider-openstack
Version: 0.13.0
Release: 1%{?dist}
Group: Applications/Internet
License: Apache Software License 2.0
URL: https://github.com/EGI-Federation/cloud-info-provider

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
* Mon Sep 11 2023 egibot <egibot@egi.eu> 0.13.0
### Added
- Add flavor name to templates (#231) (Enol Fernández)
- Support sites with URLs in the endpoints of GOCDB (#234) (Enol Fernández)
- Add new providers: AWS, Mesos and onedata (#237) (Pablo Orviz, Enol Fernández)
- Support regions in OpenStack (#229) (Enol Fernández)
- Add support for infiniband & GPUs in OpenStack (#237, #240) (Pablo Orviz, Enol Fernández)

### Fixed
- Update GitHub Actions syntax (#234) (Enol Fernández)
- Remove `/` from VO names (#230) (Enol Fernández)
- Use main as default branch (#236) (Enol Fernández)
- Improved CMDB templates (#237) (Pablo Orviz)

* Mon May 17 2021 egibot <egibot@egi.eu> 0.12.2
- Support crendential refresh without client secret (#222) (Enol Fernández)
- Add --ignore-share-errors to continue publishing data even if there are
  issues in a given share (#217, #218, 221) (Enol Fernández)
- Add timeout option to core (#219) (Enol Fernández)
- Minor fixes related to templates (#212) (Enol Fernández)
* Thu Nov 19 2020 egibot <egibot@egi.eu> 0.12.1
- Migrate from travis to GitHub Actions (#195, #198) (Enol Fernández)
- Reformatted code with black (#196) (Enol Fernández)
- Move templates inside the module (#194) (Enol Fernández)
- Publish project name and project domain name (#190) (Enol Fernández)
- Improve py3 compatibility (#189, #192) (Enol Fernández)
- Add EOSC-hub funding acknowledgement as requested by project (#188) (Enol Fernández)
- Update list of requirements for CentOS7 RPM building (#183) (Pablo Orviz)
* Wed Nov 06 2019 Baptiste Grenier <baptiste.grenier@egi.eu> 0.12.0
- Refactor SSL checks (#175). (Enol Fernández)
- Code Clean-up (#177). (Enol Fernández)
* Fri Oct 04 2019 Enol Fernández <enol.fernandez@egi.eu> 0.11.5
- Add compatibility with CentOS 7 libraries. (Enol Fernández)
- Use system CAs everywhere. (Enol Fernández)
* Tue Jul 23 2019 Enol Fernández <enol.fernandez@egi.eu> 0.11.4
- Fix get instances for volume-based instances. (Enol Fernández)
- Add external authentication plugin support. (Enol Fernández)
- Add OpenID Connect refresh plugin (OpenStack). (Enol Fernández)
- Pythonize only for Ruby dict-like strings. (Pablo Orviz)
- Fix: use is_public=None to fetch both public and private flavors. (Pablo Orviz)
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
* Mon Oct 15 2018 Baptiste Grenier <baptiste.grenier@egi.eu> 0.10.2
- Version bump (Baptiste Grenier)
* Mon Oct 01 2018 Baptiste Grenier <baptiste.grenier@egi.eu> 0.10.0
- Version bump (Baptiste Grenier)
* Wed Jun 20 2018 Baptiste Grenier <baptiste.grenier@egi.eu> 0.9.1
- First release, numbering aligned to cloud-info-provider package (Baptiste Grenier)
