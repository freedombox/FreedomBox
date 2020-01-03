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
Tests for firewall app component.
"""

from unittest.mock import call, patch

import pytest

from plinth.modules.firewall.components import Firewall


@pytest.fixture(name='empty_firewall_list', autouse=True)
def fixture_empty_firewall_list():
    """Remove all entries in firewall list before starting a test."""
    Firewall._all_firewall_components = {}


def test_init_without_arguments():
    """Test initializing the component without arguments."""
    with pytest.raises(ValueError):
        Firewall(None)

    firewall = Firewall('test-component')
    assert firewall.component_id == 'test-component'
    assert firewall.name is None
    assert firewall.ports == []
    assert not firewall.is_external
    assert len(Firewall._all_firewall_components.items()) == 1
    assert Firewall._all_firewall_components['test-component'] == firewall


def test_init():
    """Test initializing the component."""
    firewall = Firewall('test-component', 'test-name',
                        ['test-port1', 'test-port2'], is_external=True)
    assert firewall.name == 'test-name'
    assert firewall.ports == ['test-port1', 'test-port2']
    assert firewall.is_external


@patch('plinth.modules.firewall.get_port_details')
def test_port_details(get_port_details):
    """Test retrieving port details for a firewall component."""
    return_values = {'test-port1': '1234/tcp', 'test-port2': '5678/udp'}

    def get_port_details_side_effect(port):
        return return_values[port]

    get_port_details.side_effect = get_port_details_side_effect
    firewall = Firewall('test-component', ports=['test-port1', 'test-port2'])
    assert firewall.ports_details == [{
        'name': 'test-port1',
        'details': '1234/tcp'
    }, {
        'name': 'test-port2',
        'details': '5678/udp'
    }]


@patch('plinth.modules.firewall.add_service')
@patch('plinth.modules.firewall.get_enabled_services')
def test_enable(get_enabled_services, add_service):
    """Test enabling a firewall component."""
    def get_enabled_services_side_effect(zone):
        return {'internal': ['test-port1'], 'external': ['test-port2']}[zone]

    get_enabled_services.side_effect = get_enabled_services_side_effect
    # Internal
    firewall = Firewall('test-firewall-1', ports=['test-port1', 'test-port2'],
                        is_external=False)
    firewall.enable()
    calls = [call('test-port2', zone='internal')]
    add_service.assert_has_calls(calls)

    # External
    add_service.reset_mock()
    firewall = Firewall('test-firewall-2', ports=['test-port1', 'test-port2'],
                        is_external=True)
    firewall.enable()
    calls = [
        call('test-port1', zone='external'),
        call('test-port2', zone='internal')
    ]
    add_service.assert_has_calls(calls)


@patch('plinth.modules.firewall.remove_service')
@patch('plinth.modules.firewall.add_service')
@patch('plinth.modules.firewall.get_enabled_services')
def test_disable(get_enabled_services, add_service, remove_service):
    """Test disabling a firewall component."""
    Firewall('firewall-1', ports=['test-port1'], is_external=False)
    Firewall('firewall-2', ports=['test-port2'], is_external=False).enable()
    Firewall('firewall-3', ports=['test-port4'], is_external=True)
    Firewall('firewall-4', ports=['test-port5'], is_external=True).enable()

    def get_enabled_services_side_effect(zone):
        return {
            'internal': ['test-port1', 'test-port2'],
            'external': ['test-port4', 'test-port5']
        }[zone]

    get_enabled_services.side_effect = get_enabled_services_side_effect
    all_ports = [
        'test-port1', 'test-port2', 'test-port3', 'test-port4', 'test-port5',
        'test-port6'
    ]
    # Internal
    firewall = Firewall('test-firewall-1', ports=all_ports, is_external=False)
    firewall.disable()
    calls = [call('test-port1', zone='internal')]
    remove_service.assert_has_calls(calls)

    # External
    remove_service.reset_mock()
    firewall = Firewall('test-firewall-2', ports=all_ports, is_external=True)
    firewall.disable()
    calls = [
        call('test-port1', zone='internal'),
        call('test-port4', zone='external')
    ]
    remove_service.assert_has_calls(calls)


@patch('plinth.modules.firewall.get_port_details')
@patch('plinth.modules.firewall.get_enabled_services')
def test_diagnose(get_enabled_services, get_port_details):
    """Test diagnosing open/closed firewall ports."""
    def get_port_details_side_effect(port):
        return {
            'test-port1': '1234/tcp',
            'test-port2': '2345/udp',
            'test-port3': '3456/tcp',
            'test-port4': '4567/udp'
        }[port]

    def get_enabled_services_side_effect(zone):
        return {
            'internal': ['test-port1', 'test-port3'],
            'external': ['test-port2', 'test-port3']
        }[zone]

    get_enabled_services.side_effect = get_enabled_services_side_effect
    get_port_details.side_effect = get_port_details_side_effect
    firewall = Firewall('test-firewall-1', ports=['test-port1', 'test-port2'],
                        is_external=False)
    results = firewall.diagnose()
    assert results == [
        [
            'Port test-port1 (1234/tcp) available for internal networks',
            'passed'
        ],
        [
            'Port test-port1 (1234/tcp) unavailable for external networks',
            'passed'
        ],
        [
            'Port test-port2 (2345/udp) available for internal networks',
            'failed'
        ],
        [
            'Port test-port2 (2345/udp) unavailable for external networks',
            'failed'
        ]
    ]

    firewall = Firewall('test-firewall-1', ports=['test-port3', 'test-port4'],
                        is_external=True)
    results = firewall.diagnose()
    assert results == [[
        'Port test-port3 (3456/tcp) available for internal networks', 'passed'
    ], [
        'Port test-port3 (3456/tcp) available for external networks', 'passed'
    ], [
        'Port test-port4 (4567/udp) available for internal networks', 'failed'
    ], [
        'Port test-port4 (4567/udp) available for external networks', 'failed'
    ]]
