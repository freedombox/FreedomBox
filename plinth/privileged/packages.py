# SPDX-License-Identifier: AGPL-3.0-or-later
"""Wrapper to handle package installation with apt-get."""

import logging
import os
import subprocess
from collections import defaultdict
from typing import Any

import apt.cache
import apt_inst
import apt_pkg

from plinth import action_utils
from plinth import app as app_module
from plinth import module_loader
from plinth.action_utils import run_apt_command
from plinth.actions import privileged

logger = logging.getLogger(__name__)


@privileged
def update():
    """Update apt package lists."""
    returncode = run_apt_command(['update'])
    if returncode:
        raise RuntimeError(
            f'Apt command failed with return code: {returncode}')


@privileged
def install(app_id: str, packages: list[str], skip_recommends: bool = False,
            force_configuration: str | None = None, reinstall: bool = False,
            force_missing_configuration: bool = False):
    """Install packages using apt-get."""
    if force_configuration not in ('old', 'new', None):
        raise ValueError('Invalid value for force_configuration')

    try:
        _assert_managed_packages(app_id, packages)
    except Exception:
        raise PermissionError(f'Packages are not managed: {packages}')

    extra_arguments = []
    if skip_recommends:
        extra_arguments.append('--no-install-recommends')

    if force_configuration == 'old':
        extra_arguments += [
            '-o', 'Dpkg::Options::=--force-confdef', '-o',
            'Dpkg::Options::=--force-confold'
        ]
    elif force_configuration == 'new':
        extra_arguments += ['-o', 'Dpkg::Options::=--force-confnew']

    if reinstall:
        extra_arguments.append('--reinstall')

    if force_missing_configuration:
        extra_arguments += ['-o', 'Dpkg::Options::=--force-confmiss']

    subprocess.run(['dpkg', '--configure', '-a'], check=False)
    with action_utils.apt_hold_freedombox():
        run_apt_command(['--fix-broken', 'install'])
        returncode = run_apt_command(['install'] + extra_arguments + packages)

    if returncode:
        raise RuntimeError(
            f'Apt command failed with return code: {returncode}')


@privileged
def remove(app_id: str, packages: list[str], purge: bool):
    """Remove packages using apt-get."""
    try:
        _assert_managed_packages(app_id, packages)
    except Exception:
        raise PermissionError(f'Packages are not managed: {packages}')

    subprocess.run(['dpkg', '--configure', '-a'], check=False)
    with action_utils.apt_hold_freedombox():
        run_apt_command(['--fix-broken', 'install'])
        options = [] if not purge else ['--purge']
        returncode = run_apt_command(['remove'] + options + packages)

    if returncode:
        raise RuntimeError(
            f'Apt command failed with return code: {returncode}')


def _assert_managed_packages(app_id, packages):
    """Check that list of packages are in fact managed by module."""
    from plinth.package import Packages

    module_loader.load_modules()
    app_module.apps_init()
    app = app_module.App.get(app_id)
    managed_packages = []
    for component in app.get_components_of_type(Packages):
        managed_packages += component.possible_packages + component.conflicts

    for package in packages:
        assert package in managed_packages


@privileged
def is_package_manager_busy() -> bool:
    """Check whether package manager is busy.

    An exit code of zero indicates that package manager is busy.
    """
    return action_utils.is_package_manager_busy()


@privileged
def filter_conffile_packages(
        packages_list: list[str]) -> dict[str, dict[str, Any]]:
    """Return filtered list of packages which have pending conffile prompts.

    When considering which file needs a configuration file prompt, mimic the
    behavior of unattended-upgrades package. This is because when
    unattended-upgrades gives up on the package due to conffile prompts, that
    is when this logic needs to step in and perform the upgrades.

    The logic is (roughly):

      - Read /var/lib/dpkg/status file to read hashes as provided by currently
        installed version of a package.

      - Read each configuration file for the package from disk and compute
        hashes.

      - If the hashes match, package has no configuration file that got
        modified. There will be no conffile prompt.

      - If hashes don't match then check if the version of the package being
        upgraded to has the same hash as the old version of the package or in
        the new version or the package that configuration file has been
        removed. If the conditions satisfy, then there will be no conffile
        prompt. Otherwise, package will have conffile prompt.

      - A further condition for showing conffile prompt is when new package
        brings in additional configuration files not known before and some of
        which are already present on the disk and mismatch with incoming files.

    """
    apt_pkg.init()  # Read configuration that will be used later.
    packages = set(packages_list)

    status_hashes, current_versions = _get_conffile_hashes_from_status_file(
        packages)

    mismatched_hashes = _filter_matching_package_hashes(status_hashes)

    downloaded_files = _download_packages(packages)

    new_package_hashes, new_versions = \
        _get_conffile_hashes_from_downloaded_files(
            packages, downloaded_files, status_hashes, mismatched_hashes)

    packages_info = {}
    for package in packages:
        modified_conffiles = _get_modified_conffiles(
            status_hashes[package], mismatched_hashes[package],
            new_package_hashes[package])
        if not modified_conffiles:
            continue

        package_info = {
            'current_version': current_versions[package],
            'new_version': new_versions[package],
            'modified_conffiles': modified_conffiles
        }
        packages_info[package] = package_info

    return packages_info


def _get_modified_conffiles(status_hashes, mismatched_hashes,
                            new_package_hashes):
    """Return list of conffiles that will cause prompts for a package."""
    modified_conffiles = []
    for conffile, hash_value in mismatched_hashes.items():
        if conffile not in new_package_hashes:
            # Modified configuration file not present new package
            continue

        if status_hashes[conffile] == new_package_hashes[conffile]:
            # Configuration file is same in both versions of package. Conffile
            # prompt is not triggered even if the file is modified on disk.
            continue

        modified_conffiles.append(conffile)

    for conffile, hash_value in new_package_hashes.items():
        if conffile in status_hashes:
            # File is not new, it was read and matched against new/old hashes
            continue

        if not os.path.exists(conffile):
            # New configuration file brought by new package doesn't not already
            # exist on disk.
            continue

        if _get_conffile_hash(conffile) != hash_value:
            # New configuration file brought by new package doesn't match file
            # on the disk.
            #
            # If existing file is a directory, unattended-upgrades allows it,
            # we still treat it as a conffile prompt. This should be okay.
            modified_conffiles.append(conffile)

    return modified_conffiles


def _get_conffile_hashes_from_status_file(packages):
    """For each of the packages, return a dict of conffile hashes.

    Work on all packages at the same time to avoid parsing the status file
    multiple times.

    """
    package_hashes = defaultdict(dict)
    package_versions = defaultdict(lambda: None)

    status_file = apt_pkg.config.find('Dir::State::status')
    with apt_pkg.TagFile(status_file) as tag_file:
        for section in tag_file:
            package = section.get('Package')
            if package not in packages:
                continue

            hashes = _parse_conffiles_value(section.get('Conffiles', ''))
            package_hashes[package] = hashes
            package_versions[package] = section.get('Version')

    return package_hashes, package_versions


def _parse_conffiles_value(value):
    """Parse and return the list of conffiles as found in dpkg status file."""
    conffiles = {}
    for line in value.splitlines():
        parts = line.strip().split()
        if len(parts) > 2 and parts[2] == 'obsolete':
            continue

        md5sum = parts[1]
        if md5sum == 'newconffile':  # (LP: #936870)
            continue

        file_path = parts[0]
        conffiles[file_path] = md5sum

    return conffiles


def _filter_matching_package_hashes(package_hashes):
    """Return hashes of only conffiles that don't match for each package."""
    mismatched_hashes = defaultdict(dict)
    for package, hashes in package_hashes.items():
        system_hashes = {}
        for conffile, md5sum in hashes.items():
            system_md5sum = _get_conffile_hash(conffile)
            if md5sum != system_md5sum:
                system_hashes[conffile] = system_md5sum

        if system_hashes:
            mismatched_hashes[package] = system_hashes

    return mismatched_hashes


def _get_conffile_hash(conffile):
    """Return hash of a conffile in the system."""
    try:
        with open(conffile, 'rb') as file_handle:
            return apt_pkg.md5sum(file_handle)
    except (FileNotFoundError, OSError):
        return None


def _download_packages(packages):
    """Download the package for upgrade."""
    sources_list = apt_pkg.SourceList()
    sources_list.read_main_list()

    apt_pkg_cache = apt_pkg.Cache(None)  # None prevents progress messages
    apt_cache = apt.cache.Cache()
    dep_cache = apt_pkg.DepCache(apt_pkg_cache)
    for package_name in packages:
        package = apt_cache[package_name]
        if package.is_upgradable:
            dep_cache.mark_install(apt_pkg_cache[package_name], True,
                                   not package.is_auto_installed)

    package_manager = apt_pkg.PackageManager(dep_cache)
    records = apt_pkg.PackageRecords(apt_pkg_cache)
    fetcher = apt_pkg.Acquire()
    package_manager.get_archives(fetcher, sources_list, records)
    run_result = fetcher.run()
    if run_result != apt_pkg.Acquire.RESULT_CONTINUE:
        logger.error('Downloading packages failed.')
        raise RuntimeError('Downloading packages failed.')

    downloaded_files = []
    for item in fetcher.items:
        if not item.complete or item.status == item.STAT_ERROR or \
           item.status == item.STAT_AUTH_ERROR:
            continue

        if not item.is_trusted:
            continue

        if not os.path.exists(item.destfile):
            continue

        if not item.destfile.endswith('.deb'):
            continue

        downloaded_files.append(item.destfile)

    return downloaded_files


def _get_conffile_hashes_from_downloaded_files(packages, downloaded_files,
                                               status_hashes,
                                               mismatched_hashes):
    """Retrieve the conffile hashes from downloaded .deb files."""
    new_hashes = defaultdict(dict)
    new_versions = defaultdict(lambda: None)
    for downloaded_file in downloaded_files:
        try:
            package_name, hashes, new_version = \
                _get_conffile_hashes_from_downloaded_file(
                    packages, downloaded_file, status_hashes,
                    mismatched_hashes)
        except (LookupError, apt_pkg.Error, ValueError):
            continue

        new_hashes[package_name] = hashes
        new_versions[package_name] = new_version

    return new_hashes, new_versions


def _get_conffile_hashes_from_downloaded_file(packages, downloaded_file,
                                              status_hashes,
                                              mismatched_hashes):
    """Retrieve the conffile hashes from a single downloaded .deb file."""
    deb_file = apt_inst.DebFile(downloaded_file)

    control = deb_file.control.extractdata('control')

    section = apt_pkg.TagSection(control)
    package_name = section['Package']
    if package_name not in packages:
        raise ValueError

    new_version = section['Version']

    conffiles = deb_file.control.extractdata('conffiles')
    conffiles = conffiles.decode().strip().split()

    status_hashes = status_hashes.get(package_name, {})
    mismatched_hashes = mismatched_hashes.get(package_name, {})

    hashes = {}
    for conffile in conffiles:
        if conffile in status_hashes and conffile not in mismatched_hashes:
            # File already in old package and there is no change on disk.
            # Optimization to make sure we read as fewer files as possible.
            continue

        conffile_data = deb_file.data.extractdata(conffile.lstrip('/'))
        md5sum = apt_pkg.md5sum(conffile_data)
        hashes[conffile] = md5sum

    return package_name, hashes, new_version
