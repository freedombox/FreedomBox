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
import sys

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
        json_args = json.dumps({'args': args, 'kwargs': kwargs})
        return_value = superuser_run('actions', [module_name, action_name],
                                     input=json_args.encode())
        return_value = json.loads(return_value)
        if return_value['result'] == 'success':
            return return_value['return']

        module = importlib.import_module(return_value['exception']['module'])
        exception = getattr(module, return_value['exception']['name'])
        raise exception(*return_value['exception']['args'])

    return wrapper


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
    module = sys.modules[module_name]
    return module.__package__.rpartition('.')[2]
