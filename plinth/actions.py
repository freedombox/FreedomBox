# SPDX-License-Identifier: AGPL-3.0-or-later
"""Framework to run specified actions with elevated privileges."""

import argparse
import functools
import importlib
import inspect
import json
import logging
import os
import pathlib
import socket
import subprocess
import sys
import threading
import traceback
import types
import typing

from plinth import cfg, log, module_loader

EXIT_SYNTAX = 10
EXIT_PERM = 20

logger = logging.getLogger(__name__)

socket_path = '/run/freedombox/privileged.socket'


# An alias for 'str' to mark some strings as sensitive. Sensitive strings are
# not logged. Use 'type secret_str = str' when Python 3.11 support is no longer
# needed.
class secret_str(str):
    pass


def privileged(func):
    """Mark a method as allowed to be run as privileged method.

    This decorator is to mark any method as needing to be executed with
    superuser privileges. This is necessary because the primary FreedomBox
    service daemon runs as a regular user and has no special privileges. When
    performing system operations, FreedomBox service will either communicate
    with privileged daemons such as NetworkManager and systemd, or spawns a
    separate process with higher privileges. When spawning a separate process
    all the action parameters need to serialized, communicated to the process
    and then de-serialized inside the process. The return value also need to
    undergo such serialization and de-serialization. This decorator makes this
    task simpler.

    A call to a decorated method will be serialized into a sudo call (or later
    into a D-Bus call). The method arguments are turned to JSON and method is
    called with superuser privileges. As arguments are de-serialized, they are
    verified for type before the actual call as superuser. Return values are
    serialized and returned where they are de-serialized. Exceptions are also
    serialized and de-serialized. The decorator wrapper code will either return
    the value or raise exception.

    For a method to be decorated, the method must have type annotations for all
    of its parameters and should not use keyword-only arguments. It must also
    be in a module named privileged.py directly under the application similar
    to models.py, views.py and urls.py. Currently supported types are bool,
    int, float, str, dict/Dict, list/List, Optional and Union.

    Privileged methods many not output to the stdout as it interferes
    with the serialization and de-serialization process.
    """
    setattr(func, '_privileged', True)

    _check_privileged_action_arguments(func)

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        module_name = _get_privileged_action_module_name(func)
        action_name = func.__name__
        return _run_privileged_method(func, module_name, action_name, args,
                                      kwargs)

    return wrapper


def _run_privileged_method(func, module_name, action_name, args, kwargs):
    """Execute a privileged method either using a server or sudo."""
    try:
        return _run_privileged_method_on_server(func, module_name, action_name,
                                                list(args), dict(kwargs))
    except (
            NotImplementedError,  # For raw_output and run_as_user flags
            FileNotFoundError,  # When the .socket file is not present
            ConnectionRefusedError,  # When is daemon not running
            ConnectionResetError  # When daemon fails permission check
    ):
        return _run_privileged_method_as_process(func, module_name,
                                                 action_name, args, kwargs)


def _read_from_server(client_socket: socket.socket) -> bytes:
    """Read everything from a socket and return the data."""
    response = b''
    while True:
        chunk = client_socket.recv(4096)
        if not chunk:
            break

        response += chunk

    return json.loads(response)


def _request_to_server(request: dict) -> socket.socket:
    """Connect to the server and make a request."""
    request_string = json.dumps(request)
    client_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        client_socket.connect(socket_path)
        client_socket.sendall(request_string.encode('utf-8'))
        # Close the write end of the socket signaling an EOF and no more data
        # will be sent.
        client_socket.shutdown(socket.SHUT_WR)
    except Exception:
        client_socket.close()
        raise

    return client_socket


def _run_privileged_method_on_server(func, module_name, action_name, args,
                                     kwargs):
    """Execute a privileged method using a server."""
    run_as_user = kwargs.pop('_run_as_user', None)
    run_in_background = kwargs.pop('_run_in_background', False)
    raw_output = kwargs.pop('_raw_output', False)
    log_error = kwargs.pop('_log_error', True)

    if raw_output or run_as_user:
        raise NotImplementedError('Not yet implemented')

    _log_action(func, module_name, action_name, args, kwargs, run_as_user,
                run_in_background, is_server=True)

    request = {
        'module': module_name,
        'action': action_name,
        'args': args,
        'kwargs': kwargs
    }
    client_socket = _request_to_server(request)

    args = (func, module_name, action_name, args, kwargs, log_error,
            client_socket)
    if not run_in_background:
        return _wait_for_server_response(*args)

    read_thread = threading.Thread(target=_wait_for_server_response, args=args)
    read_thread.start()


def _wait_for_server_response(func, module_name, action_name, args, kwargs,
                              log_error, client_socket):
    """Wait for the server to respond and process the response."""
    try:
        return_value = _read_from_server(client_socket)
    except json.JSONDecodeError:
        logger.error('Error decoding action return value %s..%s(*%s, **%s)',
                     module_name, action_name, args, kwargs)
        raise
    finally:
        client_socket.close()

    if return_value['result'] == 'success':
        return return_value['return']

    module = importlib.import_module(return_value['exception']['module'])
    exception_class = getattr(module, return_value['exception']['name'])
    exception = exception_class(*return_value['exception']['args'])
    exception.stdout = b''
    exception.stderr = b''

    def _get_html_message():
        """Return an HTML format error that can be shown in messages."""
        from django.utils.html import format_html

        formatted_args = _format_args(func, args, kwargs)
        exception_args, stdout, stderr, traceback = _format_error(
            exception, return_value)
        return format_html('Error running action: {}..{}({}): {}({})\n{}{}{}',
                           module_name, action_name, formatted_args,
                           return_value['exception']['name'], exception_args,
                           stdout, stderr, traceback)

    exception.get_html_message = _get_html_message

    if log_error:
        formatted_args = _format_args(func, args, kwargs)
        exception_args, stdout, stderr, traceback = _format_error(
            exception, return_value)
        logger.error('Error running action %s..%s(%s): %s(%s)\n'
                     '%s%s%s', module_name, action_name, formatted_args,
                     return_value['exception']['name'], exception_args, stdout,
                     stderr, traceback)

    raise exception


def _run_privileged_method_as_process(func, module_name, action_name, args,
                                      kwargs):
    """Execute the privileged method in a sub-process with sudo."""
    run_as_user = kwargs.pop('_run_as_user', None)
    run_in_background = kwargs.pop('_run_in_background', False)
    raw_output = kwargs.pop('_raw_output', False)
    log_error = kwargs.pop('_log_error', True)

    read_fd, write_fd = os.pipe()
    os.set_inheritable(write_fd, True)

    # Prepare the command
    command = ['sudo', '--non-interactive', '--close-from', str(write_fd + 1)]
    if run_as_user:
        command += ['--user', run_as_user]

    if cfg.develop:
        command += [f'PYTHONPATH={cfg.file_root}']

    command += [
        os.path.join(cfg.actions_dir, 'actions'), module_name, action_name,
        '--write-fd',
        str(write_fd)
    ]

    proc_kwargs = {
        'stdin': subprocess.PIPE,
        'stdout': subprocess.PIPE,
        'stderr': subprocess.PIPE,
        'shell': False,
        'pass_fds': [write_fd],
    }
    if cfg.develop:
        # In development mode pass on local pythonpath to access Plinth
        proc_kwargs['env'] = {'PYTHONPATH': cfg.file_root}

    _log_action(func, module_name, action_name, args, kwargs, run_as_user,
                run_in_background, is_server=False)

    proc = subprocess.Popen(command, **proc_kwargs)
    os.close(write_fd)

    if raw_output:
        input_ = json.dumps({'args': args, 'kwargs': kwargs}).encode()
        return proc, read_fd, input_

    buffers = []
    # XXX: Use async to avoid creating a thread.
    read_thread = threading.Thread(target=_thread_reader,
                                   args=(read_fd, buffers))
    read_thread.start()

    wait_args = (func, module_name, action_name, args, kwargs, log_error, proc,
                 command, read_fd, read_thread, buffers)
    if not run_in_background:
        return _wait_for_return(*wait_args)

    wait_thread = threading.Thread(target=_wait_for_return, args=wait_args)
    wait_thread.start()


def _wait_for_return(func, module_name, action_name, args, kwargs, log_error,
                     proc, command, read_fd, read_thread, buffers):
    """Communicate with the subprocess and wait for its return."""
    json_args = json.dumps({'args': args, 'kwargs': kwargs})

    stdout, stderr = proc.communicate(input=json_args.encode())
    read_thread.join()
    if proc.returncode != 0:
        logger.error('Error executing command - %s, %s, %s', command, stdout,
                     stderr)
        raise subprocess.CalledProcessError(proc.returncode, command)

    try:
        return_value = json.loads(b''.join(buffers))
    except json.JSONDecodeError:
        logger.error('Error decoding action return value %s..%s(*%s, **%s)',
                     module_name, action_name, args, kwargs)
        raise

    if return_value['result'] == 'success':
        return return_value['return']

    module = importlib.import_module(return_value['exception']['module'])
    exception_class = getattr(module, return_value['exception']['name'])
    exception = exception_class(*return_value['exception']['args'])
    exception.stdout = stdout
    exception.stderr = stderr

    def _get_html_message():
        """Return an HTML format error that can be shown in messages."""
        from django.utils.html import format_html

        formatted_args = _format_args(func, args, kwargs)
        exception_args, stdout, stderr, traceback = _format_error(
            exception, return_value)
        return format_html('Error running action: {}..{}({}): {}({})\n{}{}{}',
                           module_name, action_name, formatted_args,
                           return_value['exception']['name'], exception_args,
                           stdout, stderr, traceback)

    exception.get_html_message = _get_html_message

    if log_error:
        formatted_args = _format_args(func, args, kwargs)
        exception_args, stdout, stderr, traceback = _format_error(
            exception, return_value)
        logger.error('Error running action %s..%s(%s): %s(%s)\n'
                     '%s%s%s', module_name, action_name, formatted_args,
                     return_value['exception']['name'], exception_args, stdout,
                     stderr, traceback)

    raise exception


def _format_args(func, args, kwargs):
    """Return a loggable representation of arguments."""
    argspec = inspect.getfullargspec(func)
    if len(args) > len(argspec.args):
        raise SyntaxError('Too many arguments')

    args_str_list = []
    for arg_index, arg_value in enumerate(args):
        arg_name = argspec.args[arg_index]
        if argspec.annotations[arg_name] in [secret_str, secret_str | None]:
            value = '****'
        else:
            value = json.dumps(arg_value)

        args_str_list.append(value)

    kwargs_str_list = []
    for arg_name, arg_value in kwargs.items():
        if argspec.annotations[arg_name] in [secret_str, secret_str | None]:
            value = "****"
        else:
            value = json.dumps(arg_value)

        kwargs_str_list.append(f'{arg_name}=' + value)

    return ', '.join(args_str_list + kwargs_str_list)


def _format_error(exception, return_value):
    """Log the exception in a readable manner."""
    exception_args = ', '.join([json.dumps(arg) for arg in exception.args])

    stdout = exception.stdout.decode()
    if stdout:
        lines = stdout.split('\n')
        lines = lines[:-1] if not lines[-1] else lines
        stdout = '\n'.join(('│ ' + line for line in lines))
        stdout = 'Stdout:\n' + stdout + '\n'

    stderr = exception.stderr.decode()
    if stderr:
        lines = stderr.split('\n')
        lines = lines[:-1] if not lines[-1] else lines
        stderr = '\n'.join(('║ ' + line for line in lines))
        stderr = 'Stderr:\n' + stderr + '\n'

    traceback = return_value['exception']['traceback']
    if traceback:
        all_lines = []
        for entry in traceback:
            lines = entry.split('\n')
            all_lines += lines[:-1] if not lines[-1] else lines

        traceback = '\n'.join(('╞ ' + line for line in all_lines))
        traceback = 'Action traceback:\n' + traceback + '\n'

    return (exception_args, stdout, stderr, traceback)


def _thread_reader(read_fd, buffers):
    """Read from the pipe in a separate thread."""
    while True:
        buffer = os.read(read_fd, 10240)
        if not buffer:
            break

        buffers.append(buffer)

    os.close(read_fd)


def _check_privileged_action_arguments(func):
    """Check that a privileged action has well defined types."""
    argspec = inspect.getfullargspec(func)
    if (argspec.varargs or argspec.varkw or argspec.kwonlyargs
            or argspec.kwonlydefaults):
        raise SyntaxError('Actions must not have variable args')

    for arg in argspec.args:
        if arg not in argspec.annotations:
            raise SyntaxError('All arguments must be annotated')

    for arg_name, arg_value in argspec.annotations.items():
        for keyword in ('password', 'passphrase', 'secret'):
            if keyword in arg_name:
                if arg_value not in [secret_str, secret_str | None]:
                    raise SyntaxError(
                        f'Argument {arg_name} should likely be a "secret_str"')


def _get_privileged_action_module_name(func):
    """Figure out the module name of a privileged action."""
    module_name = func.__module__
    while module_name:
        module_name, _, last = module_name.rpartition('.')
        if last == 'privileged':
            break

    if not module_name:
        raise ValueError('Privileged actions must be placed under a '
                         'package/module named privileged')

    return module_name.rpartition('.')[2]


def _log_action(func, module_name, action_name, args, kwargs, run_as_user,
                run_in_background, is_server):
    """Log an action in a compact format."""
    if is_server:
        prompt = '»'
    else:
        prompt = f'({run_as_user})$' if run_as_user else '#'

    suffix = '&' if run_in_background else ''
    formatted_args = _format_args(func, args, kwargs)
    logger.info('%s %s..%s(%s) %s', prompt, module_name, action_name,
                formatted_args, suffix)


class JSONEncoder(json.JSONEncoder):
    """Handle to special types that default JSON encoder does not."""

    def default(self, obj):
        """Handle special object types."""
        # When subprocess.call() fails and one of the arguments is a Path-like
        # object, the exception also contains a Path-like object.
        if isinstance(obj, pathlib.Path):
            return str(obj)

        return super().default(obj)


def privileged_main():
    """Parse arguments for the program spawned as a privileged action."""
    log.action_init()

    parser = argparse.ArgumentParser()
    parser.add_argument('module', help='Module to trigger action in')
    parser.add_argument('action', help='Action to trigger in module')
    parser.add_argument('--write-fd', type=int, default=1,
                        help='File descriptor to write output to')
    parser.add_argument('--no-args', default=False, action='store_true',
                        help='Do not read arguments from stdin')
    args = parser.parse_args()

    try:
        try:
            arguments = {'args': [], 'kwargs': {}}
            if not args.no_args:
                input_ = sys.stdin.read()
                if input_:
                    arguments = json.loads(input_)
        except json.JSONDecodeError as exception:
            raise SyntaxError('Arguments on stdin not JSON.') from exception

        return_value = _privileged_call(args.module, args.action, arguments)
        with os.fdopen(args.write_fd, 'w') as write_file_handle:
            write_file_handle.write(json.dumps(return_value, cls=JSONEncoder))
    except PermissionError as exception:
        logger.error(exception.args[0])
        sys.exit(EXIT_PERM)
    except SyntaxError as exception:
        logger.error(exception.args[0])
        sys.exit(EXIT_SYNTAX)
    except TypeError as exception:
        logger.error(exception.args[0])
        sys.exit(EXIT_SYNTAX)
    except Exception as exception:
        logger.exception(exception)
        sys.exit(1)


def privileged_handle_json_request(request_string: str) -> str:
    """Parse arguments for the program spawned as a privileged action."""

    def _parse_request() -> dict:
        """Return a JSON parsed and validated request."""
        try:
            request = json.loads(request_string)
        except json.JSONDecodeError:
            raise SyntaxError('Invalid JSON in request')

        required_parameters = [('module', str), ('action', str),
                               ('args', list), ('kwargs', dict)]

        for parameter, expected_type in required_parameters:
            if parameter not in request:
                raise TypeError(f'Missing required parameter "{parameter}"')
            if not isinstance(request[parameter], expected_type):
                raise TypeError(
                    f'Parameter "{parameter}" must be of type {expected_type.__name__}'
                )

        return request

    try:
        request = _parse_request()
        logger.info('Received request for %s..%s(..)', request['module'],
                    request['action'])
        arguments = {'args': request['args'], 'kwargs': request['kwargs']}
        return_value = _privileged_call(request['module'], request['action'],
                                        arguments)
    except (PermissionError, SyntaxError, TypeError, Exception) as exception:
        if isinstance(exception, (PermissionError, SyntaxError, TypeError)):
            logger.error(exception.args[0])
        else:
            logger.exception(exception)

        return_value = {
            'result': 'exception',
            'exception': {
                'module': type(exception).__module__,
                'name': type(exception).__name__,
                'args': exception.args,
                'traceback': traceback.format_tb(exception.__traceback__)
            }
        }

    return json.dumps(return_value, cls=JSONEncoder)


def _privileged_call(module_name, action_name, arguments):
    """Import the module and run action as superuser"""
    if '.' in module_name:
        raise SyntaxError('Invalid module name')

    cfg.read()
    if module_name == 'plinth':
        import_path = 'plinth'
    else:
        try:
            import_path = module_loader.get_module_import_path(module_name)
        except FileNotFoundError as exception:
            raise SyntaxError('Specified module not found') from exception

    try:
        module = importlib.import_module(import_path + '.privileged')
    except ModuleNotFoundError as exception:
        raise SyntaxError('Specified module not found') from exception

    try:
        action = getattr(module, action_name)
    except AttributeError as exception:
        raise SyntaxError('Specified action not found') from exception

    if not getattr(action, '_privileged', None):
        raise SyntaxError('Specified action is not privileged action')

    # Get the original function that may have been wrapped/decorated multiple
    # times
    func = action
    while True:
        try:
            func = getattr(func, '__wrapped__')
        except AttributeError:
            break

    _privileged_assert_valid_arguments(func, arguments)

    try:
        return_values = func(*arguments['args'], **arguments['kwargs'])
        return_value = {'result': 'success', 'return': return_values}
    except Exception as exception:
        return_value = {
            'result': 'exception',
            'exception': {
                'module': type(exception).__module__,
                'name': type(exception).__name__,
                'args': exception.args,
                'traceback': traceback.format_tb(exception.__traceback__)
            }
        }

    return return_value


def _privileged_assert_valid_arguments(func, arguments):
    """Check the names, types and completeness of the arguments passed."""
    # Check if arguments match types
    if not isinstance(arguments, dict):
        raise SyntaxError('Invalid arguments format')

    if 'args' not in arguments or 'kwargs' not in arguments:
        raise SyntaxError('Invalid arguments format')

    args = arguments['args']
    kwargs = arguments['kwargs']
    if not isinstance(args, list) or not isinstance(kwargs, dict):
        raise SyntaxError('Invalid arguments format')

    argspec = inspect.getfullargspec(func)
    if len(args) + len(kwargs) > len(argspec.args):
        raise SyntaxError('Too many arguments')

    no_defaults = len(argspec.args)
    if argspec.defaults:
        no_defaults -= len(argspec.defaults)

    for key in argspec.args[len(args):no_defaults]:
        if key not in kwargs:
            raise SyntaxError(f'Argument not provided: {key}')

    for key, value in kwargs.items():
        if key not in argspec.args:
            raise SyntaxError(f'Unknown argument: {key}')

        if argspec.args.index(key) < len(args):
            raise SyntaxError(f'Duplicate argument: {key}')

        _privileged_assert_valid_type(f'arg {key}', value,
                                      argspec.annotations[key])

    for index, arg in enumerate(args):
        annotation = argspec.annotations[argspec.args[index]]
        _privileged_assert_valid_type(f'arg #{index}', arg, annotation)


def _privileged_assert_valid_type(arg_name, value, annotation):
    """Assert that the type of argument value matches the annotation."""
    if annotation == typing.Any:
        return

    NoneType = type(None)
    if annotation == NoneType:
        if value is not None:
            raise TypeError('Expected None for {arg_name}')

        return

    basic_types = {bool, int, str, float}
    if annotation in basic_types:
        if not isinstance(value, annotation):
            raise TypeError(
                f'Expected type {annotation.__name__} for {arg_name}')

        return

    # secret_str should be a regular string
    if annotation == secret_str:
        if not isinstance(value, str):
            raise TypeError(f'Expected type str for {arg_name}')

        return

    # 'int | str' or 'typing.Union[int, str]'
    if (isinstance(annotation, types.UnionType)
            or getattr(annotation, '__origin__', None) == typing.Union):
        for arg in annotation.__args__:
            try:
                _privileged_assert_valid_type(arg_name, value, arg)
                return
            except TypeError:
                pass

        raise TypeError(f'Expected one of unioned types for {arg_name}')

    # 'list[int]' or 'typing.List[int]'
    if getattr(annotation, '__origin__', None) == list:
        if not isinstance(value, list):
            raise TypeError(f'Expected type list for {arg_name}')

        for index, inner_item in enumerate(value):
            _privileged_assert_valid_type(f'{arg_name}[{index}]', inner_item,
                                          annotation.__args__[0])

        return

    # 'list[dict]' or 'typing.List[dict]'
    if getattr(annotation, '__origin__', None) == dict:
        if not isinstance(value, dict):
            raise TypeError(f'Expected type dict for {arg_name}')

        for inner_key, inner_value in value.items():
            _privileged_assert_valid_type(f'{arg_name}[{inner_key}]',
                                          inner_key, annotation.__args__[0])
            _privileged_assert_valid_type(f'{arg_name}[{inner_value}]',
                                          inner_value, annotation.__args__[1])

        return

    raise TypeError('Unsupported annotation type')
