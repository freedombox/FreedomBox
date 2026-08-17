# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Tests for utilities that edit Deluge configuration files.
"""

import pytest

from plinth.modules.deluge.utils import Config

test_content = '''{
    "file": 3,
    "format": 1
}{
    "hosts": [
        [
            "c582deb3aeac48e5ba6f629ec363ea68",
            "127.0.0.1",
            58846,
            "localclient",
            "aa1d33728187a2c2516e7363d6e8fd9178abb6aa"
        ]
    ]
}'''


@pytest.fixture(name='deluge_config')
def fixture_deluge_config(tmp_path):
    """Fixture to provide a test deluge configuration file."""
    path = tmp_path / 'deluge_config'
    path.write_text(test_content)
    yield path


def test_initialization(tmp_path):
    """Test object initialization."""
    test_file = tmp_path / 'test_file'
    config = Config(str(test_file))
    assert config.file_name == str(test_file)
    assert config.file == test_file
    assert config._version is None
    assert config.content is None
    assert config._original_content is None


def test_load(deluge_config):
    """Test loading the configuration file."""
    with Config(str(deluge_config)) as config:
        assert config._version['file'] == 3
        assert config._version['format'] == 1
        assert config.content['hosts'][0][1] == '127.0.0.1'


def test_save(deluge_config):
    """Test save the configuration file."""
    with Config(str(deluge_config)) as config:
        pass

    assert deluge_config.read_text() == test_content

    with Config(str(deluge_config)) as config:
        config.content['hosts'][0][1] = '0.0.0.0'

    assert deluge_config.read_text() == test_content.replace(
        '127.0.0.1', '0.0.0.0')

    with Config(str(deluge_config)) as config:
        assert config.content['hosts'][0][1] == '0.0.0.0'

    assert deluge_config.stat().st_mode & 0o777 == 0o600
