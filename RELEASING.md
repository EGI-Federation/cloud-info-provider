# Instructions for creating a new release

Once a release and corresponding tag have been created in GitHub, packages will be
built using Travis and attached to the tag.

## Preparing the release

Steps:

* Open an issue to track the release process
* Checking changes since latest tag (using browser or CLI)
* Agreeing release version
* Preparing changelog
  * Provide main changes, with related author(s)
    * Document changes impacting deployment/configuration/usage
* Updating AUTHORS as needed
* Updating zenodo.json as needed
  * Bump version, description, authors and path to tree (at bottom)
* Merging a PR for updating build files to bump release version and changelog
* Creating a Tag in GitHub
  * Release title == Tag version, in a [semver](https://semver.org/) form like 0.42.0
  * Description is the changelog added to the build files
* Publishing release to [EGI AppDB](https://appdb.egi.eu/store/software/cloud.info.provider/releases)
* Presenting release to [EGI UMD Release Team](https://wiki.egi.eu/wiki/URT)

### Doing it from the Command Line Interface

```console
# Using hub feature: https://hub.github.com/
# git must be an alias to hub

# Create a new issue
git create -m 'Release a new pacakge version'
# Synchronize fork with upstream
git fetch upstream
git rebase upstream/master master
git checkout master
# Check latest tag
git tag --list --sort version:refname
# Compare latest tag (0.8.3 here) with master
# Using GitHub
git compare EGI-Foundation 0.8.3..master
# Using CLI
git log --abbrev-commit 0.8.3..master
# Prepare a PR to prepare version (0.9.0 here)
git checkout -b prepare-0.9.0
# Prepare a complete changelog and add it to the issue as reference
# Take care to changes in dependencies and configuration
# Depending on the changes update relevant packages
# Debian: debian/changelog: add an entry at the top
# Debian: dependencies in debian/control files
# Debian: debs/cloud-info-provider-opennebula/debian/changelog
# Debian: debs/cloud-info-provider-openstack/debian/changelog
# RHEL: bump version and dependencies at the top, add entry at the bottom
# RHEL: rpm/cloud-info-provider.spec
# RHEL: rpm/cloud-info-provider-opennebula.spec
# RHEL: rpm/cloud-info-provider-openstack.spec
# Update AUTHORS file if needed
vim AUTHORS
# Update Zenodo configuration
# Description, title, version, publication_Date
vim .zenodo.json
# Commit changes
git commit -am 'Prepare release 0.9.0'
# Push new branch to fork
git push --set-upstream origin prepare-0.9.0
# Create pull request
git pull-request
```

## Updating the entry on the AppDB

* Sign in to [project page in AppDB](https://appdb.egi.eu/store/software/cloud.info.provider/releases/)
* Create a new update (or a new release if appropriate)
  * Document description, release notes and changelog (same as the one used on
    GitHub) as needed.
  * Upload files/packages downloaded from the GitHub release
  * Publish release

## Submitting the package to EGI Cloud Middleware Distribution (CMD)

To distribute the `cloud-info-provider` as part of [Cloud Middleware
Distribution (CMD)](https://wiki.egi.eu/wiki/EGI_Cloud_Middleware_Distribution),
it's required to follow the [EGI Software provisioning
process](https://wiki.egi.eu/wiki/EGI_Software_Provisioning).

* Submitting a [GGUS ticket](https://ggus.eu/?mode=ticket_submit) to the
  `EGI Software provisioning support` Support Unit
  * Ticket category: release
  * Type of issue: Middleware
  * Assign to support unit: `EGI Software Provisioning Support`
  * Version number
  * Link to release notes (GitHub and AppDB release pages)
  * List of packages to release in CMD
