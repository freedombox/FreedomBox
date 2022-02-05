# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Test module for MediaWiki utility functions.
"""

import pathlib
import shutil
from unittest.mock import patch

import pytest

from plinth.modules import mediawiki

actions_name = 'mediawiki'
current_directory = pathlib.Path(__file__).parent


@pytest.fixture(autouse=True)
def fixture_setup_configuration(actions_module, conf_file):
    """Set configuration file path in actions module."""
    actions_module.CONF_FILE = conf_file


@pytest.fixture(name='conf_file')
def fixture_conf_file(tmp_path):
    """Uses a dummy configuration file."""
    settings_file_name = 'FreedomBoxSettings.php'
    conf_file = tmp_path / settings_file_name
    conf_file.touch()
    shutil.copyfile(
        str(current_directory / '..' / 'data' / 'etc' / 'mediawiki' /
            settings_file_name), str(conf_file))
    return str(conf_file)


@pytest.fixture(name='test_configuration', autouse=True)
def fixture_test_configuration(call_action, conf_file):
    """Use a separate MediaWiki configuration for tests.

    Uses local FreedomBoxStaticSettings.php, a temp version of
    FreedomBoxSettings.php and patches actions.superuser_run with the fixture
    call_action

    """
    data_directory = pathlib.Path(__file__).parent.parent / 'data'
    static_config_file = str(data_directory / 'etc' / 'mediawiki' /
                             mediawiki.STATIC_CONFIG_FILE.split('/')[-1])
    with patch('plinth.modules.mediawiki.STATIC_CONFIG_FILE',
               static_config_file), \
            patch('plinth.modules.mediawiki.USER_CONFIG_FILE', conf_file), \
            patch('plinth.actions.superuser_run', call_action):
        yield


def test_default_skin():
    """Test getting and setting the default skin."""
    assert mediawiki.get_default_skin() == 'timeless'
    new_skin = 'vector'
    mediawiki.set_default_skin(new_skin)
    assert mediawiki.get_default_skin() == new_skin


def test_server_url():
    """Test getting and setting $wgServer."""
    assert mediawiki.get_server_url() == 'freedombox.local'
    new_domain = 'mydomain.freedombox.rocks'
    mediawiki.set_server_url(new_domain)
    assert mediawiki.get_server_url() == new_domain
