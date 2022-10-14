# SPDX-License-Identifier: AGPL-3.0-or-later
"""Framework to run specified actions with elevated privileges."""

import functools
import importlib
import inspect
import json
import logging
import os
import subprocess
import threading

from plinth import cfg

logger = logging.getLogger(__name__)


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
        return _run_privileged_method_as_process(module_name, action_name,
                                                 args, kwargs)

    return wrapper


def _run_privileged_method_as_process(module_name, action_name, args, kwargs):
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

    _log_action(module_name, action_name, run_as_user, run_in_background)

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

    wait_args = (module_name, action_name, args, kwargs, log_error, proc,
                 command, read_fd, read_thread, buffers)
    if not run_in_background:
        return _wait_for_return(*wait_args)

    wait_thread = threading.Thread(target=_wait_for_return, args=wait_args)
    wait_thread.start()


def _wait_for_return(module_name, action_name, args, kwargs, log_error, proc,
                     command, read_fd, read_thread, buffers):
    """Communicate with the subprocess and wait for its return."""
    json_args = json.dumps({'args': args, 'kwargs': kwargs})

    output, error = proc.communicate(input=json_args.encode())
    read_thread.join()
    if proc.returncode != 0:
        logger.error('Error executing command - %s, %s, %s', command, output,
                     error)
        raise subprocess.CalledProcessError(proc.returncode, command)

    try:
        return_value = json.loads(b''.join(buffers))
    except json.JSONDecodeError:
        logger.error(
            'Error decoding action return value %s..%s(*%s, **%s): %s',
            module_name, action_name, args, kwargs, return_value)
        raise

    if return_value['result'] == 'success':
        return return_value['return']

    module = importlib.import_module(return_value['exception']['module'])
    exception_class = getattr(module, return_value['exception']['name'])
    exception = exception_class(*return_value['exception']['args'], output,
                                error)
    if log_error:
        logger.error('Error running action %s..%s(*%s, **%s): %s %s %s',
                     module_name, action_name, args, kwargs, exception,
                     exception.args, return_value['exception']['traceback'])

    raise exception


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


def _log_action(module_name, action_name, run_as_user, run_in_background):
    """Log an action in a compact format."""
    prompt = f'({run_as_user})$' if run_as_user else '#'
    suffix = '&' if run_in_background else ''
    logger.info('%s %s..%s(…) %s', prompt, module_name, action_name, suffix)
