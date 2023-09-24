# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Test module for code that runs methods are privileged actions.
"""

import typing
from unittest.mock import call as mock_call
from unittest.mock import patch

import pytest

from plinth.actions import privileged

actions_name = 'actions'


@patch('importlib.import_module')
@patch('plinth.module_loader.get_module_import_path')
@patch('os.getuid')
def test_call_syntax_checks(getuid, get_module_import_path, import_module,
                            actions_module):
    """Test that calling a method results in proper syntax checks."""
    call = actions_module._call

    # Module name validation
    getuid.return_value = 0
    with pytest.raises(SyntaxError, match='Invalid module name'):
        call('foo.bar', 'x-action', {})

    # Module import test
    get_module_import_path.return_value = 'plinth.modules.test_module'
    import_module.side_effect = ModuleNotFoundError
    with pytest.raises(SyntaxError, match='Specified module not found'):
        call('test_module', 'x-action', {})

    import_module.assert_has_calls(
        [mock_call('plinth.modules.test_module.privileged')])

    # Finding action in a module
    module = type('', (), {})
    import_module.side_effect = None
    import_module.return_value = module
    with pytest.raises(SyntaxError, match='Specified action not found'):
        call('test_module', 'x-action', {})

    # Checking if action is privileged
    def unprivileged_func():
        pass

    setattr(module, 'func', unprivileged_func)
    with pytest.raises(SyntaxError,
                       match='Specified action is not privileged action'):
        call('test-module', 'func', {})

    # Argument validation
    @privileged
    def func():
        return 'foo'

    setattr(module, 'func', func)
    with pytest.raises(SyntaxError, match='Invalid arguments format'):
        call('test-module', 'func', {})

    # Successful call
    return_value = call('test-module', 'func', {'args': [], 'kwargs': {}})
    assert return_value == {'result': 'success', 'return': 'foo'}

    # Exception call
    @privileged
    def exception_func():
        raise RuntimeError('foo exception')

    setattr(module, 'func', exception_func)
    return_value = call('test-module', 'func', {'args': [], 'kwargs': {}})
    assert return_value['result'] == 'exception'
    assert return_value['exception']['module'] == 'builtins'
    assert return_value['exception']['name'] == 'RuntimeError'
    assert return_value['exception']['args'] == ('foo exception', )
    assert isinstance(return_value['exception']['traceback'], list)
    for line in return_value['exception']['traceback']:
        assert isinstance(line, str)


def test_assert_valid_arguments(actions_module):
    """Test that checking valid arguments works."""
    assert_valid = actions_module._assert_valid_arguments

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


def test_assert_valid_type(actions_module):
    """Test that type validation works as expected."""
    assert_valid = actions_module._assert_valid_type

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
