# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Test module for MediaWiki utility functions.
"""

import pathlib
from unittest.mock import patch

import pytest

from plinth.modules import mediawiki
from plinth.modules.mediawiki import privileged

pytestmark = pytest.mark.usefixtures('mock_privileged')
current_directory = pathlib.Path(__file__).parent
privileged_modules_to_mock = ['plinth.modules.mediawiki.privileged']


@pytest.fixture(name='test_configuration', autouse=True)
def fixture_test_configuration(tmp_path):
    """Use a separate MediaWiki configuration for tests.

    FreedomBoxStaticSettings.php is used read-only from source code location.
    """
    settings_file_name = 'FreedomBoxSettings.php'
    conf_file = tmp_path / settings_file_name
    conf_file.touch()
    with (patch('plinth.modules.mediawiki.USER_CONFIG_FILE', conf_file),
          patch('plinth.modules.mediawiki.privileged.CONF_FILE', conf_file)):
        yield


def test_private_mode():
    """Test enabling/disabling private mode."""
    assert not mediawiki.get_config()['enable_private_mode']
    privileged.set_private_mode(True)
    assert mediawiki.get_config()['enable_private_mode']
    privileged.set_private_mode(False)
    assert not mediawiki.get_config()['enable_private_mode']


def test_public_registrations():
    """Test enabling/disabling public registrations."""
    assert not mediawiki.get_config()['enable_public_registrations']
    privileged.set_public_registrations(True)
    assert mediawiki.get_config()['enable_public_registrations']
    privileged.set_public_registrations(False)
    assert not mediawiki.get_config()['enable_public_registrations']


def test_default_skin():
    """Test getting and setting the default skin."""
    assert mediawiki.get_config()['default_skin'] == 'timeless'
    new_skin = 'vector'
    privileged.set_default_skin(new_skin)
    assert mediawiki.get_config()['default_skin'] == new_skin


def test_domain():
    """Test getting and setting $wgServer."""
    assert mediawiki.get_config()['domain'] == 'freedombox.local'
    new_domain = 'mydomain.freedombox.rocks'
    mediawiki.set_server_url(new_domain)
    assert mediawiki.get_config()['domain'] == new_domain


def test_site_name():
    """Test getting and setting $wgSitename."""
    assert mediawiki.get_config()['site_name'] == 'Wiki'
    new_site_name = 'My MediaWiki'
    privileged.set_site_name(new_site_name)
    assert mediawiki.get_config()['site_name'] == new_site_name
