# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Test module for actions utilities that modify configuration.

Verify that privileged actions perform as expected. See actions.py for a full
description of the expectations.

"""

import json
import os
import subprocess
import typing
from unittest.mock import Mock, call, patch

import pytest

from plinth import actions, cfg
from plinth.actions import privileged

actions_name = 'actions'


@pytest.fixture(name='popen')
def fixture_popen():
    """A fixture to patch subprocess.Popen called by privileged action."""

    with patch('subprocess.Popen') as popen:

        def call_popen(command, **kwargs):
            write_fd = int(command[8])
            if not isinstance(popen.called_with_write_fd, list):
                popen.called_with_write_fd = []

            popen.called_with_write_fd.append(write_fd)
            os.write(write_fd, bytes(popen.return_value, encoding='utf-8'))
            proc = Mock()
            proc.communicate.return_value = (b'', b'')
            proc.returncode = 0
            return proc

        popen.side_effect = call_popen
        yield popen


def test_privileged_properties():
    """Test that privileged decorator sets proper properties on the method."""

    def func():
        return

    wrapped_func = privileged(func)
    assert wrapped_func._privileged
    assert wrapped_func.__wrapped__ == func


def test_privileged_argument_vararg_check():
    """Test that privileged decorator checks for simple arguments."""

    def func_with_varargs(*_args):
        return

    def func_with_kwargs(**_kwargs):
        return

    def func_with_kwonlyargs(*_args, _kwarg):
        return

    def func_with_kwonlydefaults(*_args, _kwargs='foo'):
        return

    for func in (func_with_varargs, func_with_kwargs, func_with_kwonlyargs,
                 func_with_kwonlydefaults):
        with pytest.raises(SyntaxError):
            privileged(func)


def test_privileged_argument_annotation_check():
    """Test that privileged decorator checks for annotations to arguments."""

    def func1(_a):
        return

    def func2(_a: int, _b):
        return

    def func_valid(_a: int, _b: dict[int, str]):
        return

    for func in (func1, func2):
        with pytest.raises(SyntaxError):
            privileged(func)

    privileged(func_valid)


@patch('plinth.actions._get_privileged_action_module_name')
def test_privileged_method_call(get_module_name, popen):
    """Test that privileged method calls the superuser action properly."""

    def func_with_args(_a: int, _b: str, _c: int = 1, _d: str = 'dval',
                       _e: str = 'eval'):
        return

    get_module_name.return_value = 'tests'
    popen.return_value = json.dumps({'result': 'success', 'return': 'bar'})
    wrapped_func = privileged(func_with_args)
    return_value = wrapped_func(1, 'bval', None, _d='dnewval')
    assert return_value == 'bar'

    input_ = {'args': [1, 'bval', None], 'kwargs': {'_d': 'dnewval'}}
    input_ = json.dumps(input_)
    write_fd = popen.called_with_write_fd[0]
    close_from_fd = str(write_fd + 1)
    popen.assert_has_calls([
        call([
            'sudo', '--non-interactive', '--close-from', close_from_fd,
            cfg.actions_dir + '/actions', 'tests', 'func_with_args',
            '--write-fd',
            str(write_fd)
        ], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
             stderr=subprocess.PIPE, shell=False, pass_fds=[write_fd])
    ])


@patch('plinth.actions._get_privileged_action_module_name')
def test_privileged_method_exceptions(get_module_name, popen):
    """Test that exceptions on privileged methods are return properly."""

    def func_with_exception():
        raise TypeError('type error')

    get_module_name.return_value = 'tests'
    popen.return_value = json.dumps({
        'result': 'exception',
        'exception': {
            'module': 'builtins',
            'name': 'TypeError',
            'args': ['type error'],
            'traceback': ['']
        }
    })
    wrapped_func = privileged(func_with_exception)
    with pytest.raises(TypeError, match='type error'):
        wrapped_func()


@patch('importlib.import_module')
@patch('plinth.module_loader.get_module_import_path')
@patch('os.getuid')
def test_call_syntax_checks(getuid, get_module_import_path, import_module):
    """Test that calling a method results in proper syntax checks."""
    privileged_call = actions._privileged_call

    # Module name validation
    getuid.return_value = 0
    with pytest.raises(SyntaxError, match='Invalid module name'):
        privileged_call('foo.bar', 'x-action', {})

    # Module import test
    get_module_import_path.return_value = 'plinth.modules.test_module'
    import_module.side_effect = ModuleNotFoundError
    with pytest.raises(SyntaxError, match='Specified module not found'):
        privileged_call('test_module', 'x-action', {})

    import_module.assert_has_calls(
        [call('plinth.modules.test_module.privileged')])

    # Finding action in a module
    module = type('', (), {})
    import_module.side_effect = None
    import_module.return_value = module
    with pytest.raises(SyntaxError, match='Specified action not found'):
        privileged_call('test_module', 'x-action', {})

    # Checking if action is privileged
    def unprivileged_func():
        pass

    setattr(module, 'func', unprivileged_func)
    with pytest.raises(SyntaxError,
                       match='Specified action is not privileged action'):
        privileged_call('test-module', 'func', {})

    # Argument validation
    @actions.privileged
    def func():
        return 'foo'

    setattr(module, 'func', func)
    with pytest.raises(SyntaxError, match='Invalid arguments format'):
        privileged_call('test-module', 'func', {})

    # Successful call
    return_value = privileged_call('test-module', 'func', {
        'args': [],
        'kwargs': {}
    })
    assert return_value == {'result': 'success', 'return': 'foo'}

    # Exception call
    @actions.privileged
    def exception_func():
        raise RuntimeError('foo exception')

    setattr(module, 'func', exception_func)
    return_value = privileged_call('test-module', 'func', {
        'args': [],
        'kwargs': {}
    })
    assert return_value['result'] == 'exception'
    assert return_value['exception']['module'] == 'builtins'
    assert return_value['exception']['name'] == 'RuntimeError'
    assert return_value['exception']['args'] == ('foo exception', )
    assert isinstance(return_value['exception']['traceback'], list)
    for line in return_value['exception']['traceback']:
        assert isinstance(line, str)


def test_assert_valid_arguments():
    """Test that checking valid arguments works."""
    assert_valid = actions._privileged_assert_valid_arguments

    values = [
        None, [], 10, {}, {
            'args': []
        }, {
            'kwargs': {}
        }, {
            'args': {},
            'kwargs': {}
        }, {
            'args': [],
            'kwargs': []
        }
    ]
    for value in values:
        with pytest.raises(SyntaxError, match='Invalid arguments format'):
            assert_valid(lambda: None, value)

    def func(a: int, b: str, c: int = 3, d: str = 'foo'):
        pass

    with pytest.raises(SyntaxError, match='Too many arguments'):
        assert_valid(func, {'args': [1, 2, 3], 'kwargs': {'c': 3, 'd': 4}})

    with pytest.raises(SyntaxError, match='Too many arguments'):
        assert_valid(func, {'args': [1, 2, 3, 4, 5], 'kwargs': {}})

    with pytest.raises(SyntaxError, match='Too many arguments'):
        assert_valid(func, {
            'args': [],
            'kwargs': {
                'a': 1,
                'b': '2',
                'c': 3,
                'd': '4',
                'e': 5
            }
        })

    with pytest.raises(SyntaxError, match='Argument not provided: b'):
        assert_valid(func, {'args': [1], 'kwargs': {}})

    with pytest.raises(SyntaxError, match='Unknown argument: e'):
        assert_valid(func, {'args': [1, '2'], 'kwargs': {'e': 5}})

    with pytest.raises(SyntaxError, match='Duplicate argument: c'):
        assert_valid(func, {'args': [1, '2', 3], 'kwargs': {'c': 4}})

    with pytest.raises(TypeError, match='Expected type str for arg #1'):
        assert_valid(func, {'args': [1, 2], 'kwargs': {}})

    with pytest.raises(TypeError, match='Expected type int for arg c'):
        assert_valid(func, {'args': [1, '2'], 'kwargs': {'c': '3'}})


def test_assert_valid_type():
    """Test that type validation works as expected."""
    assert_valid = actions._privileged_assert_valid_type

    assert_valid(None, None, typing.Any)

    # Invalid values for int, str, float and Optional
    values = [[1, bool], ['foo', int], [1, str], [1, float],
              [1, typing.Optional[str]], [1, str | None],
              [1.1, typing.Union[int, str]], [1.1, int | str], [1, list],
              [1, dict], [[1], list[str]], [{
                  'a': 'b'
              }, dict[int, str]], [{
                  1: 2
              }, dict[int, str]]]
    for value in values:
        with pytest.raises(TypeError):
            assert_valid('arg', *value)

    # Valid values
    assert_valid('arg', True, bool)
    assert_valid('arg', 1, int)
    assert_valid('arg', '1', str)
    assert_valid('arg', 1.1, float)
    assert_valid('arg', None, typing.Optional[int])
    assert_valid('arg', 1, typing.Optional[int])
    assert_valid('arg', None, int | None)
    assert_valid('arg', 1, int | None)
    assert_valid('arg', 1, typing.Union[int, str])
    assert_valid('arg', '1', typing.Union[int, str])
    assert_valid('arg', 1, int | str)
    assert_valid('arg', '1', int | str)
    assert_valid('arg', [], list[int])
    assert_valid('arg', ['foo'], list[str])
    assert_valid('arg', {}, dict[int, str])
    assert_valid('arg', {1: 'foo'}, dict[int, str])
