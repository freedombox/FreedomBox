# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Unit tests for helpers of I2P application.
"""

from pathlib import Path

import pytest

from plinth.modules.i2p.helpers import TunnelEditor

DATA_DIR = Path(__file__).parent / 'data'
TUNNEL_CONF_PATH = DATA_DIR / 'i2ptunnel.config'
TUNNEL_HTTP_NAME = 'I2P HTTP Proxy'


@pytest.fixture(name='editor')
def fixture_editor():
    """Setup editor for each test."""
    return TunnelEditor(str(TUNNEL_CONF_PATH))


def test_reading_conf(editor):
    """Test reading configuration file."""
    editor.read_conf()
    assert len(editor.lines) > 1


def test_setting_idx(editor):
    """Test setting index for editing a tunnel."""
    editor.read_conf()
    assert editor.idx is None
    editor.set_tunnel_idx(TUNNEL_HTTP_NAME)
    assert editor.idx == 0


def test_setting_tunnel_props(editor):
    """Test setting a tunnel property."""
    editor.read_conf()
    editor.set_tunnel_idx('I2P HTTP Proxy')
    interface = '0.0.0.0'
    editor.set_tunnel_prop('interface', interface)
    assert editor['interface'] == interface


def test_getting_nonexistent_props(editor):
    """Test getting nonexistent property."""
    editor.read_conf()
    editor.idx = 0
    with pytest.raises(KeyError):
        _ = editor['blabla']  # noqa


def test_setting_new_props(editor):
    """Test setting new properties."""
    editor.read_conf()
    editor.idx = 0
    value = 'lol'
    prop = 'blablabla'
    editor[prop] = value
    assert editor[prop] == value
