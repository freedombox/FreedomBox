# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Test various upgrade related utilities.
"""

from unittest.mock import patch

from .. import utils


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

    list3 = '''
deb http://deb.debian.org/debian unstable main
deb http://deb.debian.org/debian trixie main
'''
    list4 = '''
deb http://deb.debian.org/debian sid main
deb http://deb.debian.org/debian trixie main
'''
    list5 = '''
deb http://deb.debian.org/debian testing main
deb http://deb.debian.org/debian trixie main
'''

    sources_list = tmp_path / 'sources.list'
    module = 'plinth.modules.upgrades.utils'
    with patch(f'{module}.sources_list', sources_list):
        sources_list.write_text(list1)
        assert utils.get_sources_list_codename() == 'bookworm'

        sources_list.write_text(list2)
        assert utils.get_sources_list_codename() is None

        sources_list.write_text(list3)
        assert utils.get_sources_list_codename() == 'unstable'

        sources_list.write_text(list4)
        assert utils.get_sources_list_codename() == 'unstable'

        sources_list.write_text(list5)
        assert utils.get_sources_list_codename() == 'testing'


@patch('subprocess.run')
def test_get_current_release(run):
    """Test that getting current release works."""
    run.return_value.stdout = b'test-release\ntest-codename\n\n'
    assert utils.get_current_release() == ('test-release', 'test-codename')


@patch('plinth.modules.upgrades.utils.get_sources_list_codename')
def test_is_distribution_unstable(get_sources_list_codename):
    """Test that checking for unstable distribution works."""
    get_sources_list_codename.return_value = 'unstable'
    assert utils.is_distribution_unstable()

    get_sources_list_codename.return_value = 'sid'
    assert utils.is_distribution_unstable()

    get_sources_list_codename.return_value = 'testing'
    assert not utils.is_distribution_unstable()


@patch('plinth.modules.upgrades.utils.get_current_release')
def test_is_distribution_rolling(get_current_release):
    """Test that checking for testing/unstable distribution works."""
    for value in ['unstable', 'testing', 'n/a']:
        get_current_release.return_value = (value, None)
        assert utils.is_distribution_rolling()

    get_current_release.return_value = ('forky', None)
    assert not utils.is_distribution_rolling()
