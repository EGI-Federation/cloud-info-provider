# DEEP-Hybrid-DataCloud Cloud Information provider

[![Build Status](https://jenkins.indigo-datacloud.eu:8080/buildStatus/icon?job=Pipeline-as-code/cloud-info-provider-deep/DEEP)](https://jenkins.indigo-datacloud.eu:8080/job/Pipeline-as-code/job/cloud-info-provider-deep/job/DEEP/)

This repository contains the new features contributed by the
DEEP-Hybrid-DataCloud project to the
[EGI Cloud Information provider](https://github.com/EGI-Foundation/cloud-info-provider).

Main contributions are expected to satisfy the resource information
requirements of the
[INDIGO PaaS orchestrator](https://github.com/indigo-dc/orchestrator). In order
to do that, the Cloud Information Provider generates JSON documents compliant
with the schema enforced by the INDIGO Configuration Management Database
(CMDB). Through a separate
[script](https://github.com/indigo-dc/cloud-info-provider-indigo),
this information is then published in the CMDB.

## Installation

Two main ways of getting `cloud-info-provider` binary on your system.

### From source

Using `pip`:

```
pip install  git+https://github.com/indigo-dc/cloud-info-provider-deep
```

### RPM and DEB packages

Available through the INDIGO software repository. Follow
[instructions](https://releases.deep-hybrid-datacloud.eu/en/latest/releases/genesis/#installation-notes)
to enable it so that it can be installed with APT or YUM repositories.

## Usage

Follow usage guidelines in the
[upstream](https://github.com/EGI-Foundation/cloud-info-provider) repository.

Any feature not available in the upstream version will be documented in the
[RELEASES](RELEASES.md) file.


## Code of conduct/Contributing guidelines

We use [git flow]() workflow for the development phase. There is however a
particular layout driven from the fact that the current repository is a fork,
which is meant for upstream contribution:

* `master` branch: in sync with upstream's master branch. Upstream contributions
(features, bug fixes) branch off this one.
* `DEEP` branch: production (long-term) branch for the DEEP features.
* release/<version>: contains the features that will take part of the `version`
release.

Any new feature must:
* Branch name prefixed by `feature/`

Any bug fix must:
* Branch name prefixed by `bugfix/`

Consequently, features and bug fixes will be added to the current
`release/<version>` branch. As a result of the release, `DEEP` branch will be
updated and a new release branch will be created.
