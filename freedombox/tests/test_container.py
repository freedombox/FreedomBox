# SPDX-License-Identifier: AGPL-3.0-or-later
"""Test component to manage a container using podman."""

from unittest.mock import call, patch

import pytest

from plinth.app import App, Info
from plinth.container import Container
from plinth.diagnostic_check import DiagnosticCheck, Result

pytestmark = pytest.mark.usefixtures('mock_privileged')
privileged_modules_to_mock = [
    'plinth.privileged', 'plinth.privileged.container',
    'plinth.privileged.service'
]


class AppTest(App):
    """Test application that contains a daemon."""

    app_id = 'test-app'


@pytest.fixture(name='container')
def fixture_container():
    app1 = AppTest()
    app1.add(Info('test-app', 1))
    container = Container('test-container', 'name1', 'image:stable', 'volume1',
                          '/volume', {'/host1': '/cont1'}, {'KEY1': 'VAL1'},
                          ['service1.service'], {'/dev/host1': '/dev/cont1'},
                          [(1234, 'tcp4')])
    app1.add(container)
    with patch('plinth.app.App.list') as app_list:
        app_list.return_value = [app1]
        yield container


def test_container_init(container):
    """Test initializing the container component."""
    component = Container('test-container', 'name1', 'image:stable', 'volume1',
                          '/volume')
    assert component.component_id == 'test-container'
    assert component.name == 'name1'
    assert component.image_name == 'image:stable'
    assert component.volume_name == 'volume1'
    assert component.volume_path == '/volume'
    assert component.volumes is None
    assert component.env is None
    assert component.binds_to is None
    assert component.devices is None
    assert component.listen_ports == []

    assert container.component_id == 'test-container'
    assert container.name == 'name1'
    assert container.image_name == 'image:stable'
    assert container.volume_name == 'volume1'
    assert container.volume_path == '/volume'
    assert container.volumes == {'/host1': '/cont1'}
    assert container.env == {'KEY1': 'VAL1'}
    assert container.binds_to == ['service1.service']
    assert container.devices == {'/dev/host1': '/dev/cont1'}
    assert container.listen_ports == [(1234, 'tcp4')]


@patch('plinth.action_utils.podman_is_enabled')
def test_container_is_enabled(podman_is_enabled, container):
    """Test checking if container is enabled."""
    podman_is_enabled.return_value = False
    assert not container.is_enabled()

    podman_is_enabled.return_value = True
    assert container.is_enabled()


@patch('plinth.action_utils.service_enable')
@patch('plinth.action_utils.podman_enable')
def test_container_enable(podman_enable, enable, container):
    """Test enabling a container component."""
    container.enable()
    assert podman_enable.mock_calls == [call('name1')]
    assert enable.mock_calls == [call('name1')]


@patch('plinth.action_utils.service_disable')
@patch('plinth.action_utils.podman_disable')
def test_container_disable(podman_disable, disable, container):
    """Test disabling a container component."""
    container.disable()
    assert podman_disable.mock_calls == [call('name1')]
    assert disable.mock_calls == [call('name1')]


@patch('plinth.action_utils.service_is_running')
def test_container_is_running(service_is_running, container):
    """Test checking of container component is running."""
    service_is_running.return_value = False
    assert not container.is_running()
    assert service_is_running.mock_calls == [call('name1')]

    service_is_running.reset_mock()
    service_is_running.return_value = True
    assert container.is_running()


@patch('plinth.action_utils.service_disable')
@patch('plinth.action_utils.service_enable')
@patch('plinth.action_utils.service_is_running')
def test_container_ensure_running(service_is_running, enable, disable,
                                  container):
    """Test checking of container component can be ensured to be running."""
    service_is_running.return_value = True
    with container.ensure_running() as state:
        assert state
        assert enable.mock_calls == []

    assert disable.mock_calls == []

    service_is_running.return_value = False
    with container.ensure_running() as state:
        assert not state
        assert enable.mock_calls == [call('name1')]

    assert disable.mock_calls == [call('name1')]


@patch('plinth.action_utils.service_disable')
@patch('plinth.action_utils.service_start')
@patch('plinth.action_utils.podman_disable')
@patch('plinth.action_utils.podman_is_enabled')
@patch('plinth.action_utils.podman_create')
def test_container_setup(podman_create, is_enabled, disable, service_start,
                         service_disable, container):
    """Test setting up the container."""
    is_enabled.return_value = True
    container.setup(0)
    assert podman_create.mock_calls == [
        call('name1', 'image:stable', 'volume1', '/volume',
             {'/host1': '/cont1'}, {'KEY1': 'VAL1'}, ['service1.service'],
             {'/dev/host1': '/dev/cont1'})
    ]
    assert service_start.mock_calls == [call('name1', check=True)]
    assert disable.mock_calls == []

    is_enabled.return_value = False
    container.setup(0)
    assert disable.mock_calls == []

    is_enabled.return_value = False
    container.setup(1)
    assert disable.mock_calls == [call('name1')]
    assert service_disable.mock_calls == [call('name1')]


@patch('plinth.action_utils.podman_uninstall')
def test_container_uninstall(podman_uninstall, container):
    """Test uninstalling the container."""
    container.uninstall()
    assert podman_uninstall.mock_calls == [
        call(container_name='name1', image_name='image:stable',
             volume_name='volume1', volume_path='/volume')
    ]


@patch('plinth.action_utils.service_is_running')
@patch('plinth.container.diagnose_port_listening')
def test_container_diagnose(diagnose_port_listening, service_is_running,
                            container):
    """Test diagnosing the container."""
    expected_results = [
        DiagnosticCheck('container-running-name1',
                        'Container {container_name} is running', Result.PASSED,
                        {'container_name': 'name1'}, 'test-container'),
        DiagnosticCheck('daemon-listening-tcp4-1234',
                        'Listening on tcp4 port 1234', Result.PASSED, {
                            'kind': 'tcp4',
                            'port': 1234
                        }, 'test-container'),
    ]
    diagnose_port_listening.return_value = expected_results[1]
    service_is_running.return_value = True
    results = container.diagnose()
    assert results == expected_results

    service_is_running.return_value = False
    expected_results[0].result = Result.FAILED
    results = container.diagnose()
    assert results == expected_results
