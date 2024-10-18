# SPDX-License-Identifier: AGPL-3.0-or-later
"""Test module for Operation and OperationsManager."""

import threading
import time
from collections import OrderedDict
from unittest.mock import Mock, call, patch

import pytest

from plinth import app

from .. import operation as operation_module
from ..notification import Notification
from ..operation import Operation, OperationsManager


class AppTest(app.App):
    app_id = 'testapp'

    def __init__(self):
        super().__init__()

        info = app.Info(self.app_id, 1, name='Test App')
        self.add(info)


@patch('plinth.operation.Operation._update_notification')
def test_operation_default_initialization(update_notification):
    """Test Operation initialization with default values."""
    target = Mock()
    operation = Operation('testid', 'testapp', 'op1', target)
    assert operation.op_id == 'testid'
    assert operation.app_id == 'testapp'
    assert operation.name == 'op1'
    assert operation.show_message
    assert not operation.show_notification
    assert operation.target == target
    assert operation.args == []
    assert operation.kwargs == {}
    assert operation.on_complete is None
    assert operation.state == Operation.State.WAITING
    assert operation._message is None
    assert operation.exception is None
    assert operation.thread_data == {}
    assert isinstance(operation.thread, threading.Thread)
    assert operation.thread._operation == operation
    update_notification.assert_has_calls([call()])


@patch('plinth.operation.Operation._update_notification')
def test_operation_initialization(update_notification):
    """Test Operation initialization with explicit values."""
    on_complete = Mock()
    operation = Operation('testid', 'testapp', 'op1', Mock(), ['arg1'],
                          {'arg2': 'value2'}, False, True,
                          {'data1': 'datavalue1'}, on_complete)
    assert not operation.show_message
    assert operation.show_notification
    assert operation.args == ['arg1']
    assert operation.kwargs == {'arg2': 'value2'}
    assert operation.on_complete == on_complete
    assert operation.state == Operation.State.WAITING
    assert operation._message is None
    assert operation.exception is None
    assert operation.thread_data == {'data1': 'datavalue1'}
    update_notification.assert_has_calls([call()])


def test_operation_str():
    """Test string representation of operation."""
    operation = Operation('testid', 'testapp', 'op1', Mock())
    assert str(operation) == 'Operation: testapp: op1'


@patch('plinth.operation.Operation._update_notification')
def test_successful_operation(update_notification):
    """Test running a operation that succeeds."""
    target = Mock()
    target.return_value = 'test-return'
    on_complete = Mock()
    operation = Operation('testid', 'testapp', 'op1', target, ['arg1'],
                          {'arg2': 'value2'}, on_complete=on_complete)
    operation.run()
    assert operation.join() == 'test-return'
    target.assert_has_calls([call('arg1', arg2='value2')])
    assert operation.state == Operation.State.COMPLETED
    assert operation.return_value == 'test-return'
    on_complete.assert_has_calls([call(operation)])
    update_notification.assert_has_calls([call(), call()])


@patch('plinth.operation.Operation._update_notification')
def test_error_operation(update_notification):
    """Test running an operation that fails."""
    target = Mock()
    target.side_effect = RuntimeError('error1')
    on_complete = Mock()
    operation = Operation('testid', 'testapp', 'op1', target, ['arg1'],
                          {'arg2': 'value2'}, on_complete=on_complete)
    operation.run()
    with pytest.raises(RuntimeError):
        operation.join()

    target.assert_has_calls([call('arg1', arg2='value2')])
    assert operation.state == Operation.State.COMPLETED
    assert operation.exception == target.side_effect
    on_complete.assert_has_calls([call(operation)])
    update_notification.assert_has_calls([call(), call()])


@patch('plinth.operation.Operation._update_notification')
def test_join_before_start(update_notification):
    """Test waiting until operation finishes.."""
    event = threading.Event()
    operation = Operation('testid', 'testapp', 'op1', Mock)
    success = []

    def _wait():
        """Wait for operation to start."""
        event.set()
        operation.join()
        success.append(True)

    thread = threading.Thread(target=_wait)
    thread.start()
    event.wait()
    time.sleep(0.1)  # Ensure that thread is waiting before we start operation.
    operation.run()
    thread.join()
    assert success


@patch('plinth.operation.Operation._update_notification')
def test_join_raises_exception(update_notification):
    """Test that joining raises exception if thread does.."""
    target = Mock()
    target.side_effect = RuntimeError('error1')
    on_complete = Mock()
    operation = Operation('testid', 'testapp', 'op1', target, ['arg1'],
                          {'arg2': 'value2'}, on_complete=on_complete)
    operation.run()
    with pytest.raises(RuntimeError):
        operation.join()


def test_getting_operation_from_thread():
    """Test that operation object can be retread from within the thread."""

    def target():
        operation = Operation.get_operation()
        operation.thread_data['test_operation'] = operation

    operation = Operation('testid', 'testapp', 'op1', target)
    operation.run()
    operation.join()
    assert operation.thread_data['test_operation'] == operation


@patch('plinth.operation.Operation._update_notification')
def test_updating_operation(update_notification):
    """Test that operation object can be updated from within the thread."""
    exception = RuntimeError('error1')

    def target():
        operation = Operation.get_operation()
        operation.on_update('message1', exception)

    operation = Operation('testid', 'testapp', 'op1', target)
    operation.run()
    with pytest.raises(RuntimeError):
        operation.join()

    assert operation._message == 'message1'
    assert operation.exception == exception
    update_notification.assert_has_calls([call(), call(), call()])


@patch('plinth.app.App.get')
def test_message(app_get):
    """Test getting the operation's message."""
    operation = Operation('testid', 'testapp', 'op1', Mock())
    operation._message = 'message1'
    operation.exception = RuntimeError('error1')
    assert operation.message == 'message1'
    assert operation.translated_message == 'message1'

    operation._message = None
    assert operation.message == 'Error: {name}: {exception}'
    assert operation.translated_message == 'Error: op1: error1'

    operation.exception = None
    operation.state = Operation.State.WAITING
    assert operation.message == 'Waiting to start: {name}'
    assert operation.translated_message == 'Waiting to start: op1'

    operation.exception = None
    operation.state = Operation.State.RUNNING
    assert operation.message == '{name}'
    assert operation.translated_message == 'op1'

    operation.exception = None
    operation.state = Operation.State.COMPLETED
    assert operation.message == 'Finished: {name}'
    assert operation.translated_message == 'Finished: op1'


@patch('plinth.app.App.get')
@pytest.mark.django_db
def test_update_notification(app_get):
    """Test that operation notification is created."""
    app_get.return_value = AppTest()
    operation = Operation('testid', 'testapp', 'op1', Mock(),
                          show_notification=True)
    note = Notification.get('testapp-operation')
    assert note.id == 'testapp-operation'
    assert note.app_id == 'testapp'
    assert note.severity == 'info'
    assert note.title == 'Test App'
    assert note.message == operation.message
    assert note.body_template == 'operation-notification.html'
    assert note.group == 'admin'
    assert not note.dismissed
    assert note.data['app_name'] == 'Test App'
    assert note.data['app_icon'] is None
    assert note.data['app_icon_filename'] is None
    assert note.data['state'] == 'waiting'
    assert note.data['exception'] is None
    assert note.data['name'] == 'translate:op1'

    operation.exception = RuntimeError()
    operation._update_notification()
    note = Notification.get('testapp-operation')
    assert note.severity == 'error'


def test_manager_global_instance():
    """Test that single global instance of operation's manager is available."""
    assert isinstance(operation_module.manager, OperationsManager)


def test_manager_init():
    """Test initializing operations manager."""
    manager = OperationsManager()
    assert manager._operations == {}
    assert manager._current_operation is None
    assert isinstance(manager._lock, threading.RLock().__class__)


def test_manager_new():
    """Test creating a new operation using a manager."""
    manager = OperationsManager()
    event = threading.Event()

    def target():
        event.wait()

    operation = manager.new('testop', 'testapp', 'op1', target)
    assert isinstance(operation, Operation)
    assert manager._current_operation == operation
    assert manager._operations == {'testop': operation}

    event.set()
    operation.join()
    assert manager._current_operation is None
    assert manager._operations == OrderedDict(testop=operation)


def test_manager_new_without_show_message():
    """Test creating an operation that does not show message."""
    manager = OperationsManager()
    event = threading.Event()

    def target():
        event.wait()

    operation = manager.new('testop', 'testapp', 'op1', target,
                            show_message=False)
    event.set()
    operation.join()
    assert manager._current_operation is None
    assert manager._operations == {}


def test_manager_new_raises():
    """Test that a new operation is always unique."""
    manager = OperationsManager()
    event1 = threading.Event()
    event2 = threading.Event()

    operation1 = manager.new('testop1', 'testapp', 'op1',
                             lambda: event1.wait())

    # Creating operation with different ID works
    operation2 = manager.new('testop2', 'testapp', 'op3', lambda: event2.set())

    assert manager._operations == OrderedDict(testop1=operation1,
                                              testop2=operation2)

    # Creating operation with same id while the operation is running/scheduled
    # throws exception
    with pytest.raises(KeyError):
        manager.new('testop1', 'testapp', 'op1', Mock())

    # Creating operation with same id after the operation is completed works.
    event1.set()  # Allow the first operation to complete
    event2.wait(10)  # Wait until the second operation has started
    operation1_new = manager.new('testop1', 'testapp', 'op1', Mock())

    assert manager._operations == OrderedDict(testop1=operation1_new,
                                              testop2=operation2)


def test_manager_scheduling():
    """Test creating a multiple operations and scheduling them."""
    manager = OperationsManager()
    event1 = threading.Event()
    event2 = threading.Event()
    event3 = threading.Event()

    operation1 = manager.new('testop1', 'testapp', 'op1', event1.wait)
    operation2 = manager.new('testop2', 'testapp', 'op2', event2.wait)
    operation3 = manager.new('testop3', 'testapp', 'op3', event3.wait)

    def _assert_is_running(current_operation):
        assert manager._current_operation == current_operation
        assert manager._operations == OrderedDict(testop1=operation1,
                                                  testop2=operation2,
                                                  testop3=operation3)
        for operation in [operation1, operation2, operation3]:
            alive = (operation == current_operation)
            assert operation.thread.is_alive() == alive

    _assert_is_running(operation1)
    event1.set()
    operation1.join()

    _assert_is_running(operation2)
    event2.set()
    operation2.join()

    _assert_is_running(operation3)
    event3.set()
    operation3.join()


def test_manager_filter():
    """Test returning filtered operations."""
    manager = OperationsManager()
    operation1 = manager.new('testop1', 'testapp1', 'op1', Mock())
    operation2 = manager.new('testop2', 'testapp1', 'op2', Mock())
    operation3 = manager.new('testop3', 'testapp2', 'op3', Mock())
    manager.filter('testapp1') == [operation1, operation2]
    manager.filter('testapp2') == [operation3]


def test_manager_collect_results():
    """Test collecting results from the manager."""
    manager = OperationsManager()
    event = threading.Event()

    operation1 = manager.new('testop1', 'testapp1', 'op1', Mock())
    operation2 = manager.new('testop2', 'testapp2', 'op2', Mock())
    operation3 = manager.new('testop3', 'testapp1', 'op3', event.wait)
    operation1.join()
    operation2.join()
    assert manager.collect_results('testapp1') == [operation1]
    assert manager._operations == OrderedDict(testop2=operation2,
                                              testop3=operation3)
    event.set()
    operation3.join()
    assert manager.collect_results('testapp1') == [operation3]
    assert manager._operations == OrderedDict(testop2=operation2)
