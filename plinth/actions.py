#
# This file is part of Plinth.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

"""Run specified actions.

Actions run commands with this contract (version 1.1):

1. (promise) Super-user actions run as root.  Normal actions do not.

2. (promise) The actions directory can't be changed at run time.

   This guarantees that we can only select from the correct set of actions.

3. (restriction) Only whitelisted actions can run.

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

      This prevents us from appending multiple (unexpected) actions to the
      call.

      $ action="echo '$options'; echo 'oops'"
      $ options="hi"
      $ $action # oops, the file system is gone!

      Arguments that fail this validation will raise a ValueError.

   D. Options can't be used to run other actions:

      $ action="echo '$options'"
      $ options="hi'; rm -rf /;'"
      $ $action # oops, the file system is gone!

      Arguments that fail this validation won't, but probably should, raise a
      ValueError.  They don't because sanitizing this case is significantly
      easier than detecting if it occurs.

      The options list is coerced into a space-separated string before being
      shell-escaped.  Option lists including shell escape characters may need
      to be unescaped on the receiving end.

   E. Actions must exist in the actions directory.

4. (promise) Options are appended to the action.

   Options can be provided as a list or strings.

5. (promise) Output and error strings are returned from the command.

6. (limitation) Providing the process with input is not possible.

   Don't expect to give the process additional input after it's started.  Any
   interaction with the spawned process must be carried out through some other
   method (maybe the process opens a socket, or something).

7. Option

"""

import logging
import os
import pipes
import subprocess

from plinth import cfg
from plinth.errors import ActionError


LOGGER = logging.getLogger(__name__)


def run(action, options=None, async=False):
    """Safely run a specific action as the current user.

    See actions._run for more information.

    """
    return _run(action, options, async, False)


def superuser_run(action, options=None, async=False):
    """Safely run a specific action as root.

    See actions._run for more information.

    """
    return _run(action, options, async, True)


def _run(action, options=None, async=False, run_as_root=False):
    """Safely run a specific action as a normal user or root.

    Actions are pulled from the actions directory.
    - options are added to the action command.
    - async: run asynchronously or wait for the command to complete.
    - run_as_root: execute the command through sudo.

    """
    if options is None:
        options = []

    # contract 3A and 3B: don't call anything outside of the actions directory.
    if os.sep in action:
        raise ValueError("Action can't contain:" + os.sep)

    cmd = os.path.join(cfg.actions_dir, action)
    if not os.path.realpath(cmd).startswith(cfg.actions_dir):
        raise ValueError("Action has to be in directory %s" % cfg.actions_dir)

    # contract 3C: interpret shell escape sequences as literal file names.
    # contract 3E: fail if the action doesn't exist or exists elsewhere.
    if not os.access(cmd, os.F_OK):
        raise ValueError("Action must exist in action directory.")

    cmd = [cmd]

    # contract: 3C, 3D: don't allow users to insert escape characters in
    # options
    if options:
        if not isinstance(options, (list, tuple)):
            options = [options]

        cmd += [pipes.quote(option) for option in options]

    # contract 1: commands can run via sudo.
    if run_as_root:
        cmd = ["sudo", "-n"] + cmd

    LOGGER.info('Executing command - %s', cmd)

    # contract 3C: don't interpret shell escape sequences.
    # contract 5 (and 6-ish).
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False)

    if not async:
        output, error = proc.communicate()
        output, error = output.decode(), error.decode()
        if proc.returncode != 0:
            LOGGER.error('Error executing command - %s, %s, %s', cmd, output,
                         error)
            raise ActionError(action, output, error)

        return output
