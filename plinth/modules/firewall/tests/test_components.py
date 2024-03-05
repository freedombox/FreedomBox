# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Tests for firewall app component.
"""

from unittest.mock import call, patch

import pytest

from plinth.app import App
from plinth.diagnostic_check import DiagnosticCheck, Result
from plinth.modules.firewall.components import (Firewall,
                                                FirewallLocalProtection)


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
    return_values = {
        'test-port1': [(1234, 'tcp')],
        'test-port2': [(5678, 'udp')]
    }

    def get_port_details_side_effect(port):
        return return_values[port]

    get_port_details.side_effect = get_port_details_side_effect
    firewall = Firewall('test-component', ports=['test-port1', 'test-port2'])
    assert firewall.ports_details == [{
        'name': 'test-port1',
        'details': [(1234, 'tcp')]
    }, {
        'name': 'test-port2',
        'details': [(5678, 'udp')]
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
            'test-port1': [(1234, 'tcp'), (1234, 'udp')],
            'test-port2': [(2345, 'udp')],
            'test-port3': [(3456, 'tcp')],
            'test-port4': [(4567, 'udp')]
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
        DiagnosticCheck(
            'firewall-port-internal-test-port1',
            'Port {name} ({details}) available for internal '
            'networks', Result.PASSED, {
                'name': 'test-port1',
                'details': '1234/tcp, 1234/udp'
            }),
        DiagnosticCheck(
            'firewall-port-external-unavailable-test-port1',
            'Port {name} ({details}) unavailable for external '
            'networks', Result.PASSED, {
                'name': 'test-port1',
                'details': '1234/tcp, 1234/udp'
            }),
        DiagnosticCheck(
            'firewall-port-internal-test-port2',
            'Port {name} ({details}) available for internal networks',
            Result.FAILED, {
                'name': 'test-port2',
                'details': '2345/udp'
            }),
        DiagnosticCheck(
            'firewall-port-external-unavailable-test-port2',
            'Port {name} ({details}) unavailable for external networks',
            Result.FAILED, {
                'name': 'test-port2',
                'details': '2345/udp'
            }),
    ]

    firewall = Firewall('test-firewall-1', ports=['test-port3', 'test-port4'],
                        is_external=True)
    results = firewall.diagnose()
    assert results == [
        DiagnosticCheck(
            'firewall-port-internal-test-port3',
            'Port {name} ({details}) available for internal networks',
            Result.PASSED, {
                'name': 'test-port3',
                'details': '3456/tcp'
            }),
        DiagnosticCheck(
            'firewall-port-external-available-test-port3',
            'Port {name} ({details}) available for external networks',
            Result.PASSED, {
                'name': 'test-port3',
                'details': '3456/tcp'
            }),
        DiagnosticCheck(
            'firewall-port-internal-test-port4',
            'Port {name} ({details}) available for internal networks',
            Result.FAILED, {
                'name': 'test-port4',
                'details': '4567/udp'
            }),
        DiagnosticCheck(
            'firewall-port-external-available-test-port4',
            'Port {name} ({details}) available for external networks',
            Result.FAILED, {
                'name': 'test-port4',
                'details': '4567/udp'
            }),
    ]


def test_local_protection_init():
    """Test initializing the local protection component."""
    component = FirewallLocalProtection('test-component', ['1234', '4567'])
    assert component.component_id == 'test-component'
    assert component.tcp_ports == ['1234', '4567']


@patch('plinth.modules.firewall.add_passthrough')
def test_local_protection_enable(add_passthrough):
    """Test enabling local protection component."""
    component = FirewallLocalProtection('test-component', ['1234', '4567'])
    component.enable()

    calls = [
        call('ipv6', '-A', 'INPUT', '-p', 'tcp', '--dport', '1234', '-j',
             'REJECT'),
        call('ipv4', '-A', 'INPUT', '-p', 'tcp', '--dport', '1234', '-j',
             'REJECT'),
        call('ipv6', '-A', 'INPUT', '-p', 'tcp', '--dport', '4567', '-j',
             'REJECT'),
        call('ipv4', '-A', 'INPUT', '-p', 'tcp', '--dport', '4567', '-j',
             'REJECT')
    ]
    add_passthrough.assert_has_calls(calls)


@patch('plinth.modules.firewall.remove_passthrough')
def test_local_protection_disable(remove_passthrough):
    """Test disabling local protection component."""
    component = FirewallLocalProtection('test-component', ['1234', '4567'])
    component.disable()

    calls = [
        call('ipv6', '-A', 'INPUT', '-p', 'tcp', '--dport', '1234', '-j',
             'REJECT'),
        call('ipv4', '-A', 'INPUT', '-p', 'tcp', '--dport', '1234', '-j',
             'REJECT'),
        call('ipv6', '-A', 'INPUT', '-p', 'tcp', '--dport', '4567', '-j',
             'REJECT'),
        call('ipv4', '-A', 'INPUT', '-p', 'tcp', '--dport', '4567', '-j',
             'REJECT')
    ]
    remove_passthrough.assert_has_calls(calls)


@patch('plinth.modules.firewall.components.FirewallLocalProtection.enable')
def test_local_protection_setup(enable):
    """Test setting up protection when updating the app."""

    class TestApp(App):
        app_id = 'test-app'
        enabled = True

        def is_enabled(self):
            return self.enabled

    app = TestApp()
    component = FirewallLocalProtection('test-component', ['1234', '4567'])
    app.add(component)

    component.setup(old_version=0)
    enable.assert_not_called()

    app.enabled = False
    component.setup(old_version=1)
    enable.assert_not_called()

    app.enabled = True
    component.setup(old_version=1)
    enable.assert_has_calls([call()])
