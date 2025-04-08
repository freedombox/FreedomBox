# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Test various part of the dist upgrade process.
"""

import re
import subprocess
from datetime import datetime as datetime_original
from datetime import timezone
from unittest.mock import call, patch

import pytest

from plinth.modules.upgrades import distupgrade

# pylint: disable=protected-access


@patch('subprocess.run')
def test_apt_run(run):
    """Test that running apt command logs properly."""
    run.return_value.returncode = 0
    args = ['command', 'arg1', 'arg2']
    distupgrade._apt_run(args)
    assert run.call_args.args == \
        (['apt-get', '--assume-yes', '--quiet=2'] + args,)
    assert not run.call_args.kwargs['stdout']

    run.return_value.returncode = 10
    with pytest.raises(RuntimeError):
        distupgrade._apt_run(args)


def test_sources_list_update(tmp_path):
    """Test that updating a sources file works."""
    original = '''
# This is a comment with 'bookworm' in it.
deb http://deb.debian.org/debian bookworm main non-free-firmware
deb-src http://deb.debian.org/debian bookworm main non-free-firmware

deb http://deb.debian.org/debian bookworm-updates main non-free-firmware
deb-src http://deb.debian.org/debian bookworm-updates main non-free-firmware

deb http://security.debian.org/debian-security/ bookworm-security main non-free-firmware
deb-src http://security.debian.org/debian-security/ bookworm-security main non-free-firmware

deb https://deb.debian.org/debian other main
deb https://deb.debian.org/debian bookwormish main
'''  # noqa: E501
    modified = '''
# This is a comment with 'bookworm' in it.
deb http://deb.debian.org/debian trixie main non-free-firmware
deb-src http://deb.debian.org/debian trixie main non-free-firmware

deb http://deb.debian.org/debian trixie-updates main non-free-firmware
deb-src http://deb.debian.org/debian trixie-updates main non-free-firmware

deb http://security.debian.org/debian-security/ trixie-security main non-free-firmware
deb-src http://security.debian.org/debian-security/ trixie-security main non-free-firmware

deb https://deb.debian.org/debian other main
deb https://deb.debian.org/debian bookwormish main
'''  # noqa: E501

    sources_list = tmp_path / 'sources.list'
    temp_sources_list = tmp_path / 'sources.list.fbx-dist-upgrade'

    module = 'plinth.modules.upgrades.distupgrade'
    with patch(f'{module}.sources_list', sources_list), \
         patch(f'{module}.temp_sources_list', temp_sources_list):
        sources_list.write_text(original)
        distupgrade._sources_list_update('bookworm', 'trixie')

        assert temp_sources_list.read_text() == modified

        original = re.sub(r'bookworm([ -])', r'stable\1', original)
        sources_list.write_text(original)
        distupgrade._sources_list_update('bookworm', 'trixie')

        assert temp_sources_list.read_text() == modified


def test_get_sources_list_codename(tmp_path):
    """Test retrieving codename from sources.list file."""
    list1 = '''
deb http://deb.debian.org/debian bookworm main non-free-firmware
deb-src http://deb.debian.org/debian bookworm main non-free-firmware

deb http://deb.debian.org/debian bookworm-updates main non-free-firmware
deb-src http://deb.debian.org/debian bookworm-updates main non-free-firmware

deb http://security.debian.org/debian-security/ bookworm-security main non-free-firmware
deb-src http://security.debian.org/debian-security/ bookworm-security main non-free-firmware
'''  # noqa: E501

    list2 = '''
deb http://deb.debian.org/debian stable main non-free-firmware
deb-src http://deb.debian.org/debian stable main non-free-firmware

deb http://deb.debian.org/debian bookworm-updates main non-free-firmware
deb-src http://deb.debian.org/debian bookworm-updates main non-free-firmware

deb http://security.debian.org/debian-security/ bookworm-security main non-free-firmware
deb-src http://security.debian.org/debian-security/ bookworm-security main non-free-firmware
'''  # noqa: E501

    sources_list = tmp_path / 'sources.list'
    module = 'plinth.modules.upgrades.distupgrade'
    with patch(f'{module}.sources_list', sources_list):
        sources_list.write_text(list1)
        assert distupgrade._get_sources_list_codename() == 'bookworm'

        sources_list.write_text(list2)
        assert distupgrade._get_sources_list_codename() is None


@patch('datetime.datetime')
@patch('plinth.modules.upgrades.get_current_release')
@patch('plinth.modules.upgrades.distupgrade._get_sources_list_codename')
@patch('plinth.action_utils.service_is_running')
@patch('plinth.modules.upgrades.utils.is_sufficient_free_space')
@patch('plinth.modules.upgrades.is_dist_upgrade_enabled')
@patch('plinth.modules.upgrades.utils.check_auto')
def test_get_status(check_auto, is_dist_upgrade_enabled,
                    is_sufficient_free_space, service_is_running,
                    get_sources_list_codename, get_current_release, datetime):
    """Test getting status of distribution upgrade."""
    # All checks fail, sources.list has 'testing' value
    check_auto.return_value = False
    is_dist_upgrade_enabled.return_value = False
    is_sufficient_free_space.return_value = False
    service_is_running.return_value = True
    get_sources_list_codename.return_value = 'testing'
    status = distupgrade.get_status()
    assert not status['updates_enabled']
    assert not status['dist_upgrade_enabled']
    assert not status['has_free_space']
    assert status['running']
    assert status['current_codename'] == 'testing'
    assert status['current_version'] is None
    assert status['current_release_date'] is None
    assert status['next_codename'] is None
    assert status['next_version'] is None
    assert status['next_release_date'] is None
    assert status['next_action'] is None

    # sources.list has mixed values
    get_sources_list_codename.return_value = None
    status = distupgrade.get_status()
    assert status['current_codename'] is None
    assert status['current_version'] is None

    # sources.list has 'unstable' value
    get_sources_list_codename.return_value = 'unstable'
    status = distupgrade.get_status()
    assert status['current_codename'] == 'unstable'
    assert status['current_version'] is None

    # sources.list has an unknown value
    get_sources_list_codename.return_value = 'x-invalid'
    get_current_release.return_value = (None, None)
    status = distupgrade.get_status()
    assert status['current_codename'] == 'x-invalid'
    assert status['current_version'] is None

    # sources.list has 'stable'
    get_sources_list_codename.return_value = 'stable'
    get_current_release.return_value = (None, 'bookworm')
    status = distupgrade.get_status()
    assert status['current_codename'] == 'bookworm'
    assert status['current_version'] == 12

    # All checks pass, next release not yet available
    check_auto.return_value = True
    is_dist_upgrade_enabled.return_value = True
    is_sufficient_free_space.return_value = True
    service_is_running.return_value = False
    get_sources_list_codename.return_value = 'bookworm'
    get_current_release.return_value = (None, 'bookworm')
    datetime.now.return_value = datetime_original(2024, 8, 10,
                                                  tzinfo=timezone.utc)
    status = distupgrade.get_status()
    assert status['updates_enabled']
    assert status['dist_upgrade_enabled']
    assert status['has_free_space']
    assert not status['running']
    assert status['current_codename'] == 'bookworm'
    assert status['current_version'] == 12
    current_date = datetime_original(2023, 6, 10, tzinfo=timezone.utc)
    assert status['current_release_date'] == current_date
    assert status['next_codename'] == 'trixie'
    assert status['next_version'] == 13
    next_date = datetime_original(2025, 8, 20, tzinfo=timezone.utc)
    assert status['next_release_date'] == next_date
    assert status['next_action'] == 'manual'

    # Distribution upgrade interrupted
    get_current_release.return_value = (None, 'trixie')
    status = distupgrade.get_status()
    assert status['next_action'] == 'continue'

    # Less than 30 days after release
    get_current_release.return_value = (None, 'bookworm')
    datetime.now.return_value = datetime_original(2025, 8, 30,
                                                  tzinfo=timezone.utc)
    status = distupgrade.get_status()
    assert status['next_action'] == 'wait_or_manual'

    # More than 30 days after release
    datetime.now.return_value = datetime_original(2025, 9, 30,
                                                  tzinfo=timezone.utc)
    status = distupgrade.get_status()
    assert status['next_action'] == 'ready'

    # Next release date not available
    get_sources_list_codename.return_value = 'trixie'
    assert distupgrade.get_status()['next_action'] is None

    # Automatic updates not enabled
    get_sources_list_codename.return_value = 'bookworm'
    check_auto.return_value = False
    assert distupgrade.get_status()['next_action'] is None

    # Distribution updates not enabled
    check_auto.return_value = True
    is_dist_upgrade_enabled.return_value = False
    assert distupgrade.get_status()['next_action'] is None

    # Not enough free space
    is_dist_upgrade_enabled.return_value = True
    is_sufficient_free_space.return_value = False
    assert distupgrade.get_status()['next_action'] is None

    # Distribution upgrade running
    is_sufficient_free_space.return_value = True
    service_is_running.return_value = True
    assert distupgrade.get_status()['next_action'] is None


@patch('subprocess.run')
@patch('plinth.modules.snapshot.is_apt_snapshots_enabled')
@patch('plinth.modules.snapshot.is_supported')
def test_snapshot_run_and_disable(is_supported, is_apt_snapshots_enabled, run):
    """Test taking a snapshot."""
    is_supported.return_value = False
    with distupgrade._snapshot_run_and_disable():
        run.assert_not_called()

    run.assert_not_called()

    is_supported.return_value = True
    is_apt_snapshots_enabled.return_value = False
    with distupgrade._snapshot_run_and_disable():
        assert run.call_args_list == [
            call(['snapper', 'create', '--description', 'before dist-upgrade'],
                 check=True)
        ]
        run.reset_mock()

    run.assert_not_called()

    is_supported.return_value = True
    is_apt_snapshots_enabled.return_value = True
    with distupgrade._snapshot_run_and_disable():
        assert run.call_args_list == [
            call(['snapper', 'create', '--description', 'before dist-upgrade'],
                 check=True),
            call([
                '/usr/share/plinth/actions/actions', 'snapshot',
                'disable_apt_snapshot'
            ], input=b'{"args": ["yes"], "kwargs": {}}', check=True)
        ]
        run.reset_mock()

    assert run.call_args_list == [
        call([
            '/usr/share/plinth/actions/actions', 'snapshot',
            'disable_apt_snapshot'
        ], input=b'{"args": ["no"], "kwargs": {}}', check=True)
    ]


@patch('plinth.action_utils.service_enable')
@patch('plinth.action_utils.service_disable')
@patch('plinth.action_utils.service_is_running')
def test_services_disable(service_is_running, service_disable, service_enable):
    """Test that disabling services works."""
    service_is_running.return_value = False
    with distupgrade._services_disable():
        service_disable.assert_not_called()

    service_enable.assert_not_called()

    service_is_running.return_value = True
    with distupgrade._services_disable():
        service_disable.call_args_list = [call('quasselcore')]

    service_enable.call_args_list = [call('quasselcore')]


@patch('subprocess.run')
@patch('subprocess.check_call')
@patch('subprocess.check_output')
def test_apt_hold_packages(check_output, check_call, run, tmp_path):
    """Test that holding apt packages works."""
    hold_flag = tmp_path / 'flag'
    run.return_value.returncode = 0
    with patch('plinth.action_utils.apt_hold_flag', hold_flag), \
         patch('plinth.modules.upgrades.distupgrade.PACKAGES_WITH_PROMPTS',
               ['package1', 'package2']):
        check_output.return_value = False
        with distupgrade._apt_hold_packages():
            assert hold_flag.exists()
            assert hold_flag.stat().st_mode & 0o117 == 0
            expected_call = [call(['apt-mark', 'hold', 'freedombox'])]
            assert check_call.call_args_list == expected_call
            expected_calls = [
                call(['apt-mark', 'hold', 'package1'], check=False),
                call(['apt-mark', 'hold', 'package2'], check=False)
            ]
            assert run.call_args_list == expected_calls
            check_call.reset_mock()
            run.reset_mock()

        expected_call = [
            call(['apt-mark', 'unhold', 'freedombox'],
                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                 check=False)
        ]
        assert run.call_args_list == expected_call
        expected_calls = [
            call(['apt-mark', 'unhold', 'package1']),
            call(['apt-mark', 'unhold', 'package2'])
        ]
        assert check_call.call_args_list == expected_calls


@patch('plinth.action_utils.debconf_set_selections')
def test_debconf_set_selections(debconf_set_selections):
    """Test that setting debconf selections works."""
    selections = 'plinth.modules.upgrades.distupgrade.PRE_DEBCONF_SELECTIONS'
    with patch(selections, []):
        distupgrade._debconf_set_selections()
        debconf_set_selections.assert_not_called()

    with patch(selections, ['selection1', 'selection2']):
        distupgrade._debconf_set_selections()
        debconf_set_selections.assert_called_with(['selection1', 'selection2'])

    distupgrade._debconf_set_selections()
    debconf_set_selections.assert_called_with(
        ['grub-pc grub-pc/install_devices_empty boolean true'])


@patch('plinth.modules.upgrades.distupgrade._apt_run')
def test_packages_remove_obsolete(apt_run):
    """Test that obsolete packages are removed."""
    distupgrade._packages_remove_obsolete()
    apt_run.assert_not_called()  # No obsolete package to remove currently.

    with patch('plinth.modules.upgrades.distupgrade.OBSOLETE_PACKAGES',
               ['tt-rss', 'searx']):
        distupgrade._packages_remove_obsolete()
        apt_run.assert_called_with(['remove', 'tt-rss', 'searx'])


@patch('plinth.modules.upgrades.distupgrade._apt_run')
def test_apt_update(apt_run):
    """Test that apt update works."""
    distupgrade._apt_update()
    apt_run.assert_called_with(['update'])


@patch('plinth.modules.upgrades.distupgrade._apt_run')
@patch('subprocess.run')
def test_apt_fix(run, apt_run):
    """Test that apt fixes work."""
    distupgrade._apt_fix()
    assert run.call_args_list == [
        call(['dpkg', '--configure', '-a'], check=False)
    ]
    assert apt_run.call_args_list == [call(['--fix-broken', 'install'])]


@patch('plinth.modules.upgrades.distupgrade._apt_run')
def test_apt_autoremove(apt_run):
    """Test that apt autoremove works."""
    distupgrade._apt_autoremove()
    apt_run.assert_called_with(['autoremove'])


@patch('plinth.modules.upgrades.distupgrade._apt_run')
def test_apt_full_upgrade(apt_run):
    """Test that apt full upgrade works."""
    apt_run.return_value = 0
    distupgrade._apt_full_upgrade()
    apt_run.assert_called_with(['full-upgrade'])


@patch('subprocess.run')
def test_unatteneded_upgrades_run(run):
    """Test that running unattended upgrades works."""
    distupgrade._unattended_upgrades_run()
    run.assert_called_with(['unattended-upgrade', '--verbose'], check=False)


@patch('plinth.action_utils.service_restart')
def test_freedombox_restart(service_restart):
    """Test that restarting freedombox service works."""
    distupgrade._freedombox_restart()
    service_restart.assert_called_with('plinth')


@patch('subprocess.run')
def test_trigger_on_complete(run):
    """Test triggering post completion process."""
    distupgrade._trigger_on_complete()
    run.assert_called_with([
        'systemd-run', '--unit=freedombox-dist-upgrade-on-complete',
        '--description=Finish up upgrade to new stable Debian release',
        '/usr/share/plinth/actions/actions', 'upgrades',
        'dist_upgrade_on_complete', '--no-args'
    ], check=True)


def test_on_complete(tmp_path):
    """Test that /etc/apt/sources.list is committed."""
    sources_list = tmp_path / 'sources.list'
    sources_list.write_text('before')
    temp_sources_list = tmp_path / 'sources.list.fbx-dist-upgrade'
    temp_sources_list.write_text('after')

    module = 'plinth.modules.upgrades.distupgrade'
    with patch(f'{module}.sources_list', sources_list), \
         patch(f'{module}.temp_sources_list', temp_sources_list):
        distupgrade.on_complete()
        assert sources_list.read_text() == 'after'
        assert not temp_sources_list.exists()
