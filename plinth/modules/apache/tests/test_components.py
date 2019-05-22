#
# This file is part of FreedomBox.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
"""
Test module for webserver components.
"""

from unittest.mock import call, patch

import pytest

from plinth.modules.apache.components import Webserver


def test_webserver_init():
    """Test that webserver component can be initialized."""
    with pytest.raises(ValueError):
        Webserver(None, None)

    webserver = Webserver('test-webserver', 'test-config', kind='module')
    assert webserver.component_id == 'test-webserver'
    assert webserver.web_name == 'test-config'
    assert webserver.kind == 'module'

    webserver = Webserver('test-webserver', None)
    assert webserver.kind == 'config'


@patch('plinth.action_utils.webserver_is_enabled')
def test_webserver_is_enabled(webserver_is_enabled):
    """Test that checking webserver configuration enabled works."""
    webserver = Webserver('test-webserver', 'test-config', kind='module')

    webserver_is_enabled.return_value = True
    assert webserver.is_enabled()
    webserver_is_enabled.assert_has_calls([call('test-config', kind='module')])

    webserver_is_enabled.reset_mock()
    webserver_is_enabled.return_value = False
    assert not webserver.is_enabled()
    webserver_is_enabled.assert_has_calls([call('test-config', kind='module')])


@patch('plinth.actions.superuser_run')
def test_webserver_enable(superuser_run):
    """Test that enabling webserver configuration works."""
    webserver = Webserver('test-webserver', 'test-config', kind='module')

    webserver.enable()
    superuser_run.assert_has_calls([
        call('apache', ['enable', '--name', 'test-config', '--kind', 'module'])
    ])


@patch('plinth.actions.superuser_run')
def test_webserver_disable(superuser_run):
    """Test that disabling webserver configuration works."""
    webserver = Webserver('test-webserver', 'test-config', kind='module')

    webserver.disable()
    superuser_run.assert_has_calls([
        call('apache',
             ['disable', '--name', 'test-config', '--kind', 'module'])
    ])
