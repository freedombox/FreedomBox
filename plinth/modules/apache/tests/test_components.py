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

from plinth.modules.apache.components import Uwsgi, Webserver


def test_webserver_init():
    """Test that webserver component can be initialized."""
    with pytest.raises(ValueError):
        Webserver(None, None)

    webserver = Webserver('test-webserver', 'test-config', kind='module',
                          urls=['url1', 'url2'])
    assert webserver.component_id == 'test-webserver'
    assert webserver.web_name == 'test-config'
    assert webserver.kind == 'module'
    assert webserver.urls == ['url1', 'url2']

    webserver = Webserver('test-webserver', None)
    assert webserver.kind == 'config'
    assert webserver.urls == []


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


@patch('plinth.action_utils.diagnose_url')
@patch('plinth.action_utils.diagnose_url_on_all')
def test_webserver_diagnose(diagnose_url_on_all, diagnose_url):
    """Test running diagnostics."""
    def on_all_side_effect(url, check_certificate):
        return [('test-result-' + url, 'success')]

    def side_effect(url, check_certificate):
        return ('test-result-' + url, 'success')

    diagnose_url_on_all.side_effect = on_all_side_effect
    diagnose_url.side_effect = side_effect
    webserver = Webserver('test-webserver', 'test-config',
                          urls=['{host}url1', 'url2'])
    results = webserver.diagnose()
    assert results == [('test-result-{host}url1', 'success'),
                       ('test-result-url2', 'success')]
    diagnose_url_on_all.assert_has_calls(
        [call('{host}url1', check_certificate=False)])
    diagnose_url.assert_has_calls([call('url2', check_certificate=False)])


def test_uwsgi_init():
    """Test that uWSGI component can be initialized."""
    with pytest.raises(ValueError):
        Uwsgi(None, None)

    uwsgi = Uwsgi('test-uwsgi', 'test-config')
    assert uwsgi.component_id == 'test-uwsgi'
    assert uwsgi.uwsgi_name == 'test-config'


@patch('plinth.action_utils.service_is_enabled')
@patch('plinth.action_utils.uwsgi_is_enabled')
def test_uwsgi_is_enabled(uwsgi_is_enabled, service_is_enabled):
    """Test that checking uwsgi configuration enabled works."""
    uwsgi = Uwsgi('test-uwsgi', 'test-config')

    uwsgi_is_enabled.return_value = True
    service_is_enabled.return_value = True
    assert uwsgi.is_enabled()
    uwsgi_is_enabled.assert_has_calls([call('test-config')])
    service_is_enabled.assert_has_calls([call('uwsgi')])

    service_is_enabled.return_value = False
    assert not uwsgi.is_enabled()

    uwsgi_is_enabled.return_value = False
    assert not uwsgi.is_enabled()

    service_is_enabled.return_value = False
    assert not uwsgi.is_enabled()


@patch('plinth.actions.superuser_run')
def test_uwsgi_enable(superuser_run):
    """Test that enabling uwsgi configuration works."""
    uwsgi = Uwsgi('test-uwsgi', 'test-config')

    uwsgi.enable()
    superuser_run.assert_has_calls(
        [call('apache', ['uwsgi-enable', '--name', 'test-config'])])


@patch('plinth.actions.superuser_run')
def test_uwsgi_disable(superuser_run):
    """Test that disabling uwsgi configuration works."""
    uwsgi = Uwsgi('test-uwsgi', 'test-config')

    uwsgi.disable()
    superuser_run.assert_has_calls(
        [call('apache', ['uwsgi-disable', '--name', 'test-config'])])


@patch('plinth.action_utils.service_is_running')
@patch('plinth.action_utils.uwsgi_is_enabled')
def test_uwsgi_is_running(uwsgi_is_enabled, service_is_running):
    """Test checking whether uwsgi is running with a configuration."""
    uwsgi = Uwsgi('test-uwsgi', 'test-config')

    uwsgi_is_enabled.return_value = True
    service_is_running.return_value = True
    assert uwsgi.is_running()
    uwsgi_is_enabled.assert_has_calls([call('test-config')])
    service_is_running.assert_has_calls([call('uwsgi')])

    uwsgi_is_enabled.return_value = False
    service_is_running.return_value = True
    assert not uwsgi.is_running()

    uwsgi_is_enabled.return_value = True
    service_is_running.return_value = False
    assert not uwsgi.is_running()

    uwsgi_is_enabled.return_value = False
    service_is_running.return_value = False
    assert not uwsgi.is_running()
