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
Test module for component managing system daemons and other systemd units.
"""

import socket
from unittest.mock import Mock, call, patch

import pytest

from plinth.app import App, FollowerComponent
from plinth.daemon import Daemon, app_is_running, diagnose_port_listening


@pytest.fixture(name='daemon')
def fixture_daemon():
    """Create a test daemon object."""
    return Daemon('test-daemon', 'test-unit')


def test_initialization():
    """Test that component is initialized properly."""
    with pytest.raises(ValueError):
        Daemon(None, None)

    daemon = Daemon('test-daemon', 'test-unit')
    assert daemon.component_id == 'test-daemon'
    assert daemon.unit == 'test-unit'
    assert not daemon.strict_check
    assert daemon.listen_ports == []

    listen_ports = [(345, 'tcp4'), (123, 'udp')]
    daemon = Daemon('test-daemon', 'test-unit', strict_check=True,
                    listen_ports=listen_ports)
    assert daemon.strict_check
    assert daemon.listen_ports == listen_ports


@patch('plinth.action_utils.service_is_enabled')
def test_is_enabled(service_is_enabled, daemon):
    """Test that daemon enabled check works."""
    service_is_enabled.return_value = True
    assert daemon.is_enabled()
    service_is_enabled.assert_has_calls(
        [call('test-unit', strict_check=False)])

    service_is_enabled.return_value = False
    assert not daemon.is_enabled()

    service_is_enabled.reset_mock()
    daemon.strict_check = True
    daemon.is_enabled()
    service_is_enabled.assert_has_calls([call('test-unit', strict_check=True)])


@patch('plinth.actions.superuser_run')
def test_enable(superuser_run, daemon):
    """Test that enabling the daemon works."""
    daemon.enable()
    superuser_run.assert_has_calls([call('service', ['enable', 'test-unit'])])


@patch('plinth.actions.superuser_run')
def test_disable(superuser_run, daemon):
    """Test that disabling the daemon works."""
    daemon.disable()
    superuser_run.assert_has_calls([call('service', ['disable', 'test-unit'])])


@patch('plinth.action_utils.service_is_running')
def test_is_running(service_is_running, daemon):
    """Test that checking that the daemon is running works."""
    service_is_running.return_value = True
    assert daemon.is_running()
    service_is_running.assert_has_calls([call('test-unit')])

    service_is_running.return_value = False
    assert not daemon.is_running()


@patch('plinth.action_utils.service_is_running')
@patch('plinth.daemon.diagnose_port_listening')
def test_diagnose(port_listening, service_is_running, daemon):
    """Test running diagnostics."""
    def side_effect(port, kind):
        return [f'test-result-{port}-{kind}', 'passed']

    daemon = Daemon('test-daemon', 'test-unit', listen_ports=[(8273, 'tcp4'),
                                                              (345, 'udp')])
    port_listening.side_effect = side_effect
    service_is_running.return_value = True
    results = daemon.diagnose()
    assert results == [['Service test-unit is running', 'passed'],
                       ['test-result-8273-tcp4', 'passed'],
                       ['test-result-345-udp', 'passed']]
    port_listening.assert_has_calls([call(8273, 'tcp4'), call(345, 'udp')])
    service_is_running.assert_has_calls([call('test-unit')])

    service_is_running.return_value = False
    results = daemon.diagnose()
    assert results[0][1] == 'failed'


@patch('plinth.action_utils.service_is_running')
def test_app_is_running(service_is_running):
    """Test that checking whether app is running works."""
    daemon1 = Daemon('test-daemon-1', 'test-unit-1')
    daemon2 = FollowerComponent('test-daemon-2', 'test-unit-2')
    daemon2.is_running = Mock()

    follower1 = FollowerComponent('test-follower-1')

    class TestApp(App):
        """Test app"""
        app_id = 'test-app'

    app = TestApp()
    app.add(daemon1)
    app.add(daemon2)
    app.add(follower1)

    service_is_running.return_value = True
    daemon2.is_running.return_value = False
    assert not app_is_running(app)

    service_is_running.return_value = False
    daemon2.is_running.return_value = False
    assert not app_is_running(app)

    service_is_running.return_value = True
    daemon2.is_running.return_value = True
    assert app_is_running(app)


@patch('psutil.net_connections')
def test_diagnose_port_listening(connections):
    """Test running port listening diagnostics test."""
    connections.return_value = [
        Mock(status='LISTEN', laddr=('0.0.0.0', 1234), family=socket.AF_INET),
        Mock(status='ESTABLISHED', laddr=('0.0.0.0', 2345),
             family=socket.AF_INET),
        Mock(raddr=(), laddr=('0.0.0.0', 3456), family=socket.AF_INET),
        Mock(raddr=('1.1.1.1', 53), laddr=('0.0.0.0', 4567),
             family=socket.AF_INET),
        Mock(status='LISTEN', laddr=('::1', 5678), familiy=socket.AF_INET6),
        Mock(status='LISTEN', laddr=('::', 6789), familiy=socket.AF_INET6),
        Mock(raddr=(), laddr=('::1', 5678), familiy=socket.AF_INET6),
        Mock(raddr=(), laddr=('::', 6789), familiy=socket.AF_INET6),
    ]

    # Check that message is correct
    results = diagnose_port_listening(1234)
    assert results == ['Listening on tcp port 1234', 'passed']
    results = diagnose_port_listening(1234, 'tcp', '0.0.0.0')
    assert results == ['Listening on tcp port 0.0.0.0:1234', 'passed']

    # Failed results
    results = diagnose_port_listening(4321)
    assert results == ['Listening on tcp port 4321', 'failed']
    results = diagnose_port_listening(4321, 'tcp', '0.0.0.0')
    assert results == ['Listening on tcp port 0.0.0.0:4321', 'failed']

    # Check if psutil call is being made with right argument
    results = diagnose_port_listening(1234, 'tcp')
    connections.assert_called_with('tcp')
    results = diagnose_port_listening(1234, 'tcp4')
    connections.assert_called_with('tcp')
    results = diagnose_port_listening(1234, 'tcp6')
    connections.assert_called_with('tcp6')
    results = diagnose_port_listening(3456, 'udp')
    connections.assert_called_with('udp')
    results = diagnose_port_listening(3456, 'udp4')
    connections.assert_called_with('udp')
    results = diagnose_port_listening(3456, 'udp6')
    connections.assert_called_with('udp6')

    # TCP
    assert diagnose_port_listening(1234)[1] == 'passed'
    assert diagnose_port_listening(1000)[1] == 'failed'
    assert diagnose_port_listening(2345)[1] == 'failed'
    assert diagnose_port_listening(1234, 'tcp', '0.0.0.0')[1] == 'passed'
    assert diagnose_port_listening(1234, 'tcp', '1.1.1.1')[1] == 'failed'
    assert diagnose_port_listening(1234, 'tcp6')[1] == 'passed'
    assert diagnose_port_listening(1234, 'tcp4')[1] == 'passed'
    assert diagnose_port_listening(6789, 'tcp4')[1] == 'passed'
    assert diagnose_port_listening(5678, 'tcp4')[1] == 'failed'

    # UDP
    assert diagnose_port_listening(3456, 'udp')[1] == 'passed'
    assert diagnose_port_listening(3000, 'udp')[1] == 'failed'
    assert diagnose_port_listening(4567, 'udp')[1] == 'failed'
    assert diagnose_port_listening(3456, 'udp', '0.0.0.0')[1] == 'passed'
    assert diagnose_port_listening(3456, 'udp', '1.1.1.1')[1] == 'failed'
    assert diagnose_port_listening(3456, 'udp6')[1] == 'passed'
    assert diagnose_port_listening(3456, 'udp4')[1] == 'passed'
    assert diagnose_port_listening(6789, 'udp4')[1] == 'passed'
    assert diagnose_port_listening(5678, 'udp4')[1] == 'failed'
