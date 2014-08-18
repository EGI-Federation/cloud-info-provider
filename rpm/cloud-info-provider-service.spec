Name:           cloud-info-provider-service
Version:        0.3
Release:        1%{?dist}
Summary:        Information provider for Cloud Compute and Cloud Storage services for BDII.

Group:          Applications/Internet
License:        GPLv3
URL:            https://github.com/EGI-FCTF/BDIIscripts
Source0:        BDIIscripts-%{version}.zip
BuildRoot:      %(mktemp -ud %{_tmppath}/%{name}-%{version}-%{release}-XXXXXX)
BuildArch:      noarch

#BuildRequires:  cp
Requires:       PyYAML bdii python-argparse python-yaml

%description
Information provider for Cloud COmpute and Cloud Storage services for BDII. It supports static information specification, OpenNebula nad OpenStack cloud middleware. The provider uses GLUE 2.0 EGI Cloud Profile to publish the information.

%prep
%setup -q -n BDIIscripts-%{version}

%build

%install
rm -rf %{buildroot}
mkdir -p %{buildroot}/opt/cloud-info-provider/
cp -r cloud_bdii etc bin %{buildroot}/opt/cloud-info-provider/
mkdir -p %{buildroot}/usr/bin
ln -s /opt/cloud-info-provider/bin/cloud-info-provider-service.py %{buildroot}/usr/bin/cloud-info-provider-service
chmod +x %{buildroot}/opt/cloud-info-provider/bin/cloud-info-provider-service.py

%clean
rm -rf %{buildroot}

%files
%defattr(-,root,root,-)
/opt/cloud-info-provider
/usr/bin/cloud-info-provider-service

%changelog
* Mon Aug 18 2014 Release 0.3 - Salvatore Pinto
- Fixed OpenNebula provider (thanks to Boris Parak)
* Tue Jul 25 2014 Release 0.2 - Salvatore Pinto
- Added rpm packaging and bin wrapper
- Added possibility to setup options via YAML
- Added retreival of Site name from BDII configuration
- Moved production_level to service and endpoint objects
- Changed basic tree for cloud services to GLUE2GroupID=cloud
- Added OpenNebula and OpenNebulaROCCI drivers
- Small changes to OpenStack driver (Marketplace information from glancepush, rewritten template, possibility to filter images without marketplace ID)
- Removed support for Tenant ID (insthead of Tenant name) for retro-compatibility with older versions of novaclient libraries
* Wed May 28 2014 Release 0.1 - Alvaro Lopez Garcia
- First release
