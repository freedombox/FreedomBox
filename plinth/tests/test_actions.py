# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Test module for actions utilities that modify configuration.

Verify that privileged actions perform as expected. See actions.py for a full
description of the expectations.

"""

import json
import os
import subprocess
from unittest.mock import Mock, call, patch

import pytest

from plinth import cfg
from plinth.actions import privileged


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
