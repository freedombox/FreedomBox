# SPDX-License-Identifier: AGPL-3.0-or-later
"""Run specified actions.

Actions run commands with this contract (version 1.1):

1. (promise) Super-user actions run as root.  Normal actions do not.

2. (promise) The actions directory can't be changed at run time.

   This guarantees that we can only select from the correct set of actions.

3. (restriction) Only specifically allowed actions can run.

   A. Scripts in a directory above the actions directory can't be run.

      Arguments (and options) can't coerce the system to run actions in
      directories above the actions directory.

      Arguments that fail this validation will raise a ValueError.

   B. Scripts in a directory beneath the actions directory can't be run.

      Arguments (and options) can't coerce the system to run actions in
      sub-directories of the actions directory.

      (An important side-effect of this is that the system will not try to
       follow symlinks to other action directories.)

      Arguments that fail this validation will raise a ValueError.

   C. Only one action can be called at a time.

      This prevents us from appending multiple (unexpected) actions to
      the call.  Any special shell characters in the action name will
      simply be treated as the action itself when trying to search for
      an action.  The action will then not be found.

      $ action="echo '$options'; echo 'oops'"
      $ options="hi"
      $ $action # oops, the file system is gone!

      Arguments that fail this validation will raise a ValueError.

   D. Options can't be used to run other actions:

      $ action="echo '$options'"
      $ options="hi'; rm -rf /;'"
      $ $action # oops, the file system is gone!

      Any option that tries to include special shell characters will
      simply be treated as an option with special characters and will
      not be interpreted by the shell.

      Any call wishing to include special shell characters in options
      list does not need to escape them.  They are taken care of.  The
      option string is passed to the action exactly as it is passed in.

   E. Actions must exist in the actions directory.

4. (promise) Options are passed as arguments to the action.

   Options can be provided as a list or as a tuple.

5. (promise) Output is returned from the command.  In case of an
   error, ActionError is raised with action, output and error strings
   as arguments.

6. (limitation) Providing the process with input is not possible.

   Don't expect to give the process additional input after it's started.  Any
   interaction with the spawned process must be carried out through some other
   method (maybe the process opens a socket, or something).

7. Option

"""

import functools
import importlib
import inspect
import json
import logging
import os
import re
import shlex
import subprocess
import threading

from plinth import cfg
from plinth.errors import ActionError

logger = logging.getLogger(__name__)


def run(action, options=None, input=None, run_in_background=False):
    """Safely run a specific action as the current user.

    See actions._run for more information.
    """
    return _run(action, options, input, run_in_background, False)


def superuser_run(action, options=None, input=None, run_in_background=False,
                  log_error=True):
    """Safely run a specific action as root.

    See actions._run for more information.
    """
    return _run(action, options, input, run_in_background, True,
                log_error=log_error)


def run_as_user(action, options=None, input=None, run_in_background=False,
                become_user=None):
    """Run a command as a different user.

    If become_user is None, run as current user.
    """
    return _run(action, options, input, run_in_background, False, become_user)


def _run(action, options=None, input=None, run_in_background=False,
         run_as_root=False, become_user=None, log_error=True):
    """Safely run a specific action as a normal user or root.

    Actions are pulled from the actions directory.

    - options are added to the action command.

    - input: data (as bytes) that will be sent to the action command's stdin.

    - run_in_background: run asynchronously or wait for the command to
      complete.

    - run_as_root: execute the command through sudo.

    """
    if options is None:
        options = []

    # Contract 3A and 3B: don't call anything outside of the actions directory.
    if os.sep in action:
        raise ValueError('Action cannot contain: ' + os.sep)

    cmd = os.path.join(cfg.actions_dir, action)
    if not os.path.realpath(cmd).startswith(cfg.actions_dir):
        raise ValueError('Action has to be in directory %s' % cfg.actions_dir)

    # Contract 3C: interpret shell escape sequences as literal file names.
    # Contract 3E: fail if the action doesn't exist or exists elsewhere.
    if not os.access(cmd, os.F_OK):
        raise ValueError('Action must exist in action directory.')

    cmd = [cmd]

    # Contract: 3C, 3D: don't allow shell special characters in
    # options be interpreted by the shell.  When using
    # subprocess.Popen with list invocation and not shell invocation,
    # escaping is unnecessary as each argument is passed directly to
    # the command and not parsed by a shell.
    if options:
        if not isinstance(options, (list, tuple)):
            raise ValueError('Options must be list or tuple.')

        cmd += list(options)  # No escaping necessary

    # Contract 1: commands can run via sudo.
    sudo_call = []
    if run_as_root:
        sudo_call = ['sudo', '-n']
    elif become_user:
        sudo_call = ['sudo', '-n', '-u', become_user]

    if cfg.develop and sudo_call:
        # Passing 'env' does not work with sudo, so append the PYTHONPATH
        # as part of the command
        sudo_call += ['PYTHONPATH=%s' % cfg.file_root]

    if sudo_call:
        cmd = sudo_call + cmd

    _log_command(cmd)

    # Contract 3C: don't interpret shell escape sequences.
    # Contract 5 (and 6-ish).
    kwargs = {
        'stdin': subprocess.PIPE,
        'stdout': subprocess.PIPE,
        'stderr': subprocess.PIPE,
        'shell': False,
    }
    if cfg.develop:
        # In development mode pass on local pythonpath to access Plinth
        kwargs['env'] = {'PYTHONPATH': cfg.file_root}

    proc = subprocess.Popen(cmd, **kwargs)

    if not run_in_background:
        output, error = proc.communicate(input=input)
        output, error = output.decode(), error.decode()
        if proc.returncode != 0:
            if log_error:
                logger.error('Error executing command - %s, %s, %s', cmd,
                             output, error)
            raise ActionError(action, output, error)

        return output

    return proc


def _log_command(cmd):
    """Log a command with special pretty formatting to catch the eye."""
    cmd = list(cmd)  # Make a copy of the command not to affect the original

    prompt = '$'
    user = ''
    if cmd and cmd[0] == 'sudo':
        cmd = cmd[1:]
        prompt = '#'

        # Drop -n argument to sudo
        if cmd and cmd[0] == '-n':
            cmd = cmd[1:]

        # Capture username separately
        if len(cmd) > 1 and cmd[0] == '-u':
            prompt = '$'
            user = cmd[1]
            cmd = cmd[2:]

        # Drop environmental variables set via sudo
        while cmd and re.match(r'.*=.*', cmd[0]):
            cmd = cmd[1:]

    # Strip the command's prefix
    if cmd:
        cmd[0] = cmd[0].split('/')[-1]

    # Shell escape and join command arguments
    cmd = ' '.join([shlex.quote(part) for part in cmd])

    logger.info('%s%s %s', user, prompt, cmd)


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
