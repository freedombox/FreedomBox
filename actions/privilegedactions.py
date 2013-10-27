#! /usr/bin/env python
# -*- mode: python; mode: auto-fill; fill-column: 80 -*-

"""Run specified privileged actions as root.

Privileged actions run commands with this contract (version 1.0):

1. (promise) Privileged actions run as root.

2. (promise) The actions directory can't be changed at run time.

   This guarantees that we can only select from the correct set of actions.

3. (restriction) Only whitelisted privileged actions can run.

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

      This prevents us from appending multiple (unexpected) actions to the call.

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

   E. Actions must exist in the actions directory.

4. (promise) Options are appended to the action.

5. (promise) Output and error strings are returned from the command.

6. (limitation) Providing the process with input is not possible.

   Don't expect to give the process additional input after it's started.  Any
   interaction with the spawned process must be carried out through some other
   method (maybe the process opens a socket, or something).

"""

import contract
import os
import pipes
import shlex
import subprocess

contract.checkmod(__name__)

def privilegedaction_run(action, options = None):
    """Safely run a specific action as root.

    pre:
        os.sep not in actions
    inv:
        True # Actions directory hasn't changed.  It's hardcoded :)

    """
    DIRECTORY = "actions"

    # contract 3A and 3B: don't call anything outside of the actions directory.
    if os.sep in action:
        raise ValueError("Action can't contain:" + os.sep)
    if not isinstance(options, str):
        raise ValueError("Options must be a string and cannot be a list.")

    # contract: 3C, 3D: don't allow users to insert escape characters.
    action = pipes.quote(action)
    options = pipes.quote(options)

    cmd = DIRECTORY + os.sep + action

    # contract 3C: interpret shell escape sequences as literal file names.
    # contract 3E: fail if the action doesn't exist or exists elsewhere.
    if not os.access(cmd, os.F_OK):
        raise ValueError("Action must exist in action directory.")

    cmd = ["sudo", "-n", cmd]

    # contract 4.
    if options:
        cmd.extend(shlex.split(options))

    # contract 3C: don't interpret shell escape sequences.
    # contract 5 (and 6-ish).
    output, error = \
        subprocess.Popen(cmd,
                         stdout = subprocess.PIPE,
                         stderr= subprocess.PIPE,
                         shell=False).communicate()
    return output, error
