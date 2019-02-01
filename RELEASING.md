# Instructions for creating a new release

Once a release and corresponding tag have been created in GitHub, packages will be
built using Travis and attached to the tag.

## Preparing the release

Steps:

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
# Synchronize fork with upstream
git fetch upstream
git rebase upstream/master master
git checkout master
# Check latest tag
git tag --list
# Compare latest tag (0.8.3 here) with master
# hub feature, showing diff in GitHub
# https://hub.github.com/
git compare EGI-FCTF 0.8.3..master
# In the CLI
git log --abbrev-commit 0.8.3..master
# Prepare a PR to prepare version (0.9.0 here)
git checkout -b prepare-0.9.0
# Prepare a complete changelog in a text file
# Take care to changes in dependencies and configuration
# Depending on the changes update relevant packages
# Debian: debian/changelog: add an entry at the top
# Debian: changelog: add an entry at the top
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
