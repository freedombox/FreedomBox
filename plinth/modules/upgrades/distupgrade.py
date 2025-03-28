# SPDX-License-Identifier: AGPL-3.0-or-later
"""Perform distribution upgrade."""

import contextlib
import logging
import pathlib
import subprocess
import time
from typing import Generator

import augeas

from plinth import action_utils
from plinth.modules import snapshot as snapshot_module

from . import utils

logger = logging.getLogger(__name__)

OBSOLETE_PACKAGES: list[str] = []

PACKAGES_WITH_PROMPTS = ['firewalld', 'minidlna', 'radicale']

PRE_DEBCONF_SELECTIONS: list[str] = [
    # Tell grub-pc to continue without installing grub again.
    'grub-pc grub-pc/install_devices_empty boolean true'
]

sources_list = pathlib.Path('/etc/apt/sources.list')
temp_sources_list = pathlib.Path('/etc/apt/sources.list.fbx-dist-upgrade')


def _apt_run(arguments: list[str], enable_triggers: bool = False):
    """Run an apt command and ensure that output is written to stdout."""
    return action_utils.run_apt_command(arguments, stdout=None,
                                        enable_triggers=enable_triggers)


def _sources_list_update(old_codename: str, new_codename: str):
    """Change the distribution in /etc/apt/sources.list."""
    logger.info('Upgrading from %s to %s...', old_codename, new_codename)
    aug = augeas.Augeas(flags=augeas.Augeas.NO_LOAD +
                        augeas.Augeas.NO_MODL_AUTOLOAD)
    aug.transform('aptsources', str(sources_list))
    aug.set('/augeas/context', '/files' + str(sources_list))
    aug.set('/augeas/save', 'newfile')  # Save to a new file
    aug.load()

    for match_ in aug.match('*'):
        dist_path = match_ + '/distribution'
        dist = aug.get(dist_path)
        if dist in (old_codename, 'stable'):
            aug.set(dist_path, new_codename)
        elif dist and (dist.startswith(old_codename + '-')
                       or dist.startswith('stable' + '-')):
            new_value = new_codename + '-' + dist.partition('-')[2]
            aug.set(dist_path, new_value)

    aug.save()

    aug_path = sources_list.with_suffix('.list.augnew')
    aug_path.rename(temp_sources_list)


def _get_new_codename(test_upgrade: bool) -> str | None:
    """Return the codename for the next release."""
    release_file_dist = 'stable'
    if test_upgrade:
        release_file_dist = 'testing'

    url = utils.RELEASE_FILE_URL.format(release_file_dist)
    command = ['curl', '--silent', '--location', '--fail', url]
    protocol = utils.get_http_protocol()
    if protocol == 'tor+http':
        command.insert(0, 'torsocks')
        logging.info('Package download over Tor is enabled.')

    try:
        output = subprocess.check_output(command).decode()
    except (subprocess.CalledProcessError, FileNotFoundError):
        logging.warning('Error while checking for new %s release',
                        release_file_dist)
    else:
        for line in output.split('\n'):
            if line.startswith('Codename:'):
                return line.split()[1]

    return None


def _check(test_upgrade: bool = False) -> tuple[str, str]:
    """Check if a distribution upgrade be performed.

    Check for new stable release, if updates are enabled, and if there is
    enough free space for the dist upgrade.

    If test_upgrade is True, also check for upgrade to testing.

    Return (boolean, string) indicating if the upgrade is ready, and a reason
    if not.
    """
    if not utils.check_auto():
        raise RuntimeError('upgrades-not-enabled')

    if not utils.is_sufficient_free_space():
        raise RuntimeError('not-enough-free-space')

    if action_utils.service_is_running('freedombox-dist-upgrade'):
        raise RuntimeError('found-previous')

    from plinth.modules.upgrades import get_current_release
    release, old_codename = get_current_release()
    if release in ['unstable', 'testing', 'n/a']:
        raise RuntimeError(f'already-{release}')

    new_codename = _get_new_codename(test_upgrade)
    if not new_codename:
        raise RuntimeError('codename-not-found')

    if new_codename == old_codename:
        raise RuntimeError(f'already-{old_codename}')

    return old_codename, new_codename


@contextlib.contextmanager
def _snapshot_run_and_disable() -> Generator[None, None, None]:
    """Take a snapshot if supported and enabled, then disable snapshots.

    Snapshots shall be re-enabled, if originally enabled, on exiting this
    context manager..
    """
    if not snapshot_module.is_supported():
        logger.info('Snapshots are not supported, skipping taking a snapshot.')
        yield
        return

    reenable = False
    try:
        logger.info('Taking a snapshot before dist upgrade...')
        subprocess.run([
            '/usr/share/plinth/actions/actions', 'snapshot', 'create',
            '--no-args'
        ], check=True)
        aug = snapshot_module.load_augeas()
        if snapshot_module.is_apt_snapshots_enabled(aug):
            logger.info('Disabling apt snapshots during dist upgrade...')
            subprocess.run([
                '/usr/share/plinth/actions/actions',
                'snapshot',
                'disable_apt_snapshot',
            ], input='{"args": ["yes"], "kwargs": {}}'.encode(), check=True)
            reenable = True
        else:
            logger.info('Apt snapshots already disabled.')

        yield
    finally:
        if reenable:
            logger.info('Re-enabling apt snapshots...')
            subprocess.run([
                '/usr/share/plinth/actions/actions', 'snapshot',
                'disable_apt_snapshot'
            ], input='{"args": ["no"], "kwargs": {}}'.encode(), check=True)
        else:
            logger.info('Not re-enabling apt snapshots, as they were disabled '
                        'before dist upgrade.')


@contextlib.contextmanager
def _services_disable():
    """Disable services that are seriously impacted by the upgrade."""
    # If quassel is running during dist upgrade, it may be restarted
    # several times. This causes IRC users to rapidly leave/join
    # channels. Stop quassel for the duration of the dist upgrade.
    logger.info('Stopping quassel service during dist upgrade...')
    with action_utils.service_ensure_stopped('quasselcore'):
        yield
        logger.info('Re-enabling quassel service if previously enabled...')


@contextlib.contextmanager
def _apt_hold_packages():
    """Apt hold some packages during dist upgrade."""
    packages = PACKAGES_WITH_PROMPTS
    packages_string = ', '.join(packages)

    # Hold freedombox package during entire dist upgrade.
    logger.info('Holding freedombox package...')
    with action_utils.apt_hold_freedombox():
        # Hold packages known to have conffile prompts. FreedomBox service
        # will handle their upgrade later.
        logger.info('Holding packages with conffile prompts: %s...',
                    packages_string)
        with action_utils.apt_hold(packages):
            yield
            logger.info(
                'Releasing holds on packages with conffile prompts: %s...',
                packages_string)

        logger.info('Releasing hold on freedombox package...')


def _debconf_set_selections() -> None:
    """Pre-set debconf selections if they are needed for dist upgrade."""
    if PRE_DEBCONF_SELECTIONS:
        logger.info('Setting debconf selections: %s', PRE_DEBCONF_SELECTIONS)
        action_utils.debconf_set_selections(PRE_DEBCONF_SELECTIONS)


def _packages_remove_obsolete() -> None:
    """Remove obsolete packages.

    These may prevent other packages from upgrading.
    """
    if OBSOLETE_PACKAGES:
        logger.info('Removing packages: %s...', OBSOLETE_PACKAGES)
        _apt_run(['remove'] + OBSOLETE_PACKAGES)


def _apt_update(enable_triggers: bool = False):
    """Run 'apt update'."""
    logger.info('Updating Apt cache...')
    _apt_run(['update'], enable_triggers=enable_triggers)


def _apt_fix():
    """Try to fix any problems with apt/dpkg before the upgrade."""
    logger.info('Fixing any broken apt/dpkg states...')
    subprocess.run(['dpkg', '--configure', '-a'], check=False)
    _apt_run(['--fix-broken', 'install'])


def _apt_autoremove():
    """Run 'apt autoremove'."""
    logger.info('Running apt autoremove...')
    _apt_run(['autoremove'])


def _apt_full_upgrade():
    """Run and check if apt upgrade was successful."""
    logger.info('Running apt full-upgrade...')
    returncode = _apt_run(['full-upgrade'])
    if returncode:
        raise RuntimeError(
            'Apt full-upgrade was not successful. Distribution upgrade '
            'will be retried at a later time.')


def _unattended_upgrades_run():
    """Run unattended-upgrade once more.

    To handle upgrading the freedombox package.
    """
    logger.info('Running unattended-upgrade...')
    subprocess.run(['unattended-upgrade', '--verbose'], check=False)


def _freedombox_restart():
    """Restart FreedomBox service.

    To ensure it is using the latest dependencies.
    """
    logger.info('Restarting FreedomBox service...')
    action_utils.service_restart('plinth')


def _wait():
    """Wait for 10 minutes before performing remaining actions."""
    logger.info('Waiting for 10 minutes...')
    time.sleep(10 * 60)


def _trigger_on_complete():
    """Trigger the on complete step in a separate service."""
    # The dist-upgrade process will be run /etc/apt/sources.list file bind
    # mounted on with a modified file. So, moving modified file to the original
    # file will not be possible. For that, we need to launch a new process with
    # a different systemd service (which does not have the bind mounts).
    logger.info('Triggering on-complete to commit sources.lists')
    subprocess.run([
        'systemd-run', '--unit=freedombox-dist-upgrade-on-complete',
        '--description=Finish up upgrade to new stable Debian release',
        '/usr/share/plinth/actions/actions', 'upgrades',
        'dist_upgrade_on_complete', '--no-args'
    ], check=True)


def _logging_setup():
    """Log to journal via console logging.

    We need to capture all console logs created by apt and other commands and
    redirect them to journal. This is the default behavior when launching a
    service with systemd-run.

    Avoid double logging to the journal by removing the systemd journal as a
    log handler..
    """
    logging.getLogger(None).removeHandler('journal')


def perform():
    """Perform upgrade to next release of Debian."""
    _logging_setup()
    with _snapshot_run_and_disable(), \
         _services_disable(), \
         _apt_hold_packages():
        _apt_update()
        _apt_fix()
        _debconf_set_selections()
        _packages_remove_obsolete()
        _apt_full_upgrade()
        _apt_autoremove()

    _unattended_upgrades_run()
    _freedombox_restart()
    _wait()
    _apt_update(enable_triggers=True)
    _trigger_on_complete()


def start_service(test_upgrade: bool):
    """Create dist upgrade service and start it."""
    # Cleanup old service
    old_service_path = pathlib.Path(
        '/run/systemd/system/freedombox-dist-upgrade.service')
    if old_service_path.exists():
        old_service_path.unlink(missing_ok=True)
        action_utils.service_daemon_reload()

    old_codename, new_codename = _check(test_upgrade)

    _sources_list_update(old_codename, new_codename)

    args = [
        '--unit=freedombox-dist-upgrade',
        '--description=Upgrade to new stable Debian release',
        '--property=KillMode=process', '--property=TimeoutSec=12hr',
        f'--property=BindPaths={temp_sources_list}:{sources_list}'
    ]
    subprocess.run(['systemd-run'] + args + [
        'systemd-inhibit', '/usr/share/plinth/actions/actions', 'upgrades',
        'dist_upgrade', '--no-args'
    ], check=True)


def on_complete():
    """Perform cleanup operations."""
    _logging_setup()
    logger.info('Dist upgrade complete.')
    logger.info('Committing changes to /etc/apt/sources.list')
    temp_sources_list.rename(sources_list)
