# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Test various part of the dist upgrade process.
"""

import re
import subprocess
from unittest.mock import call, patch

import pytest

from plinth.modules.upgrades import distupgrade

# pylint: disable=protected-access


@patch('subprocess.run')
def test_apt_run(run):
    """Test that running apt command logs properly."""
    run.return_value.returncode = 10
    args = ['command', 'arg1', 'arg2']
    assert distupgrade._apt_run(args) == 10
    assert run.call_args.args == \
        (['apt-get', '--assume-yes', '--quiet=2'] + args,)
    assert not run.call_args.kwargs['stdout']


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
    sources_list.write_text(original)
    with patch('plinth.modules.upgrades.distupgrade.SOURCES_LIST',
               str(sources_list)):
        distupgrade._sources_list_update('bookworm', 'trixie')

    assert sources_list.read_text() == modified

    original = re.sub(r'bookworm([ -])', r'stable\1', original)
    sources_list.write_text(original)
    with patch('plinth.modules.upgrades.distupgrade.SOURCES_LIST',
               str(sources_list)):
        distupgrade._sources_list_update('bookworm', 'trixie')

    assert sources_list.read_text() == modified


@patch('plinth.modules.upgrades.utils.get_http_protocol')
@patch('subprocess.check_output')
def test_get_new_codename(check_output, get_http_protocol):
    """Test that getting a new distro codename works."""
    get_http_protocol.return_value = 'http'
    check_output.return_value = b'''
Suite: testing
Codename: trixie
Description: Debian Testing distribution
'''
    assert distupgrade._get_new_codename(False) == 'trixie'
    check_output.assert_called_with([
        'curl', '--silent', '--location', '--fail',
        'https://deb.debian.org/debian/dists/stable/Release'
    ])

    assert distupgrade._get_new_codename(True) == 'trixie'
    check_output.assert_called_with([
        'curl', '--silent', '--location', '--fail',
        'https://deb.debian.org/debian/dists/testing/Release'
    ])

    check_output.side_effect = FileNotFoundError('curl not found')
    assert not distupgrade._get_new_codename(True)


@patch('plinth.modules.upgrades.distupgrade._get_new_codename')
@patch('plinth.modules.upgrades.get_current_release')
@patch('plinth.action_utils.service_is_running')
@patch('plinth.modules.upgrades.utils.is_sufficient_free_space')
@patch('plinth.modules.upgrades.utils.check_auto')
def test_check(check_auto, is_sufficient_free_space, service_is_running,
               get_current_release, get_new_codename):
    """Test checking for available dist upgrade."""
    check_auto.return_value = False
    with pytest.raises(RuntimeError, match='upgrades-not-enabled'):
        distupgrade._check()

    check_auto.return_value = True
    is_sufficient_free_space.return_value = False
    with pytest.raises(RuntimeError, match='not-enough-free-space'):
        distupgrade._check()

    is_sufficient_free_space.return_value = True
    service_is_running.return_value = True
    with pytest.raises(RuntimeError, match='found-previous'):
        distupgrade._check()

    service_is_running.return_value = False
    for release in ['unstable', 'testing', 'n/a']:
        get_current_release.return_value = (release, release)
        with pytest.raises(RuntimeError, match=f'already-{release}'):
            distupgrade._check()

    get_current_release.return_value = ('12', 'bookworm')
    get_new_codename.return_value = None
    with pytest.raises(RuntimeError, match='codename-not-found'):
        distupgrade._check()
        get_new_codename.assert_called_with(False)

        distupgrade._check(True)
        get_new_codename.assert_called_with(True)

    get_new_codename.return_value = 'bookworm'
    with pytest.raises(RuntimeError, match='already-bookworm'):
        distupgrade._check()

    get_new_codename.return_value = 'trixie'
    assert distupgrade._check() == ('bookworm', 'trixie')


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
            call([
                '/usr/share/plinth/actions/actions', 'snapshot', 'create',
                '--no-args'
            ], check=True)
        ]
        run.reset_mock()

    run.assert_not_called()

    is_supported.return_value = True
    is_apt_snapshots_enabled.return_value = True
    with distupgrade._snapshot_run_and_disable():
        assert run.call_args_list == [
            call([
                '/usr/share/plinth/actions/actions', 'snapshot', 'create',
                '--no-args'
            ], check=True),
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

    apt_run.return_value = 1
    with pytest.raises(RuntimeError):
        distupgrade._apt_full_upgrade()


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


@patch('time.sleep')
def test_wait(sleep):
    """Test that sleeping works."""
    distupgrade._wait()
    sleep.assert_called_with(600)
