# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Test module for MediaWiki utility functions.
"""

import pathlib
import shutil
from unittest.mock import patch

import pytest

from plinth.modules import mediawiki
from plinth.modules.mediawiki import privileged

pytestmark = pytest.mark.usefixtures('mock_privileged')
current_directory = pathlib.Path(__file__).parent
privileged_modules_to_mock = ['plinth.modules.mediawiki.privileged']


@pytest.fixture(autouse=True)
def fixture_setup_configuration(conf_file):
    """Set configuration file path in actions module."""
    privileged.CONF_FILE = conf_file


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
def fixture_test_configuration(conf_file):
    """Use a separate MediaWiki configuration for tests.

    Uses local FreedomBoxStaticSettings.php, a temp version of
    FreedomBoxSettings.php

    """
    data_directory = pathlib.Path(__file__).parent.parent / 'data'
    static_config_file = str(data_directory / 'etc' / 'mediawiki' /
                             mediawiki.STATIC_CONFIG_FILE.split('/')[-1])
    with patch('plinth.modules.mediawiki.STATIC_CONFIG_FILE',
               static_config_file), \
         patch('plinth.modules.mediawiki.USER_CONFIG_FILE', conf_file):
        yield


def test_default_skin():
    """Test getting and setting the default skin."""
    assert mediawiki.get_default_skin() == 'timeless'
    new_skin = 'vector'
    privileged.set_default_skin(new_skin)
    assert mediawiki.get_default_skin() == new_skin


def test_server_url():
    """Test getting and setting $wgServer."""
    assert mediawiki.get_server_url() == 'freedombox.local'
    new_domain = 'mydomain.freedombox.rocks'
    mediawiki.set_server_url(new_domain)
    assert mediawiki.get_server_url() == new_domain


def test_site_name():
    """Test getting and setting $wgSitename."""
    assert mediawiki.get_site_name() == 'Wiki'
    new_site_name = 'My MediaWiki'
    privileged.set_site_name(new_site_name)
    assert mediawiki.get_site_name() == new_site_name
