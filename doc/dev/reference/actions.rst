.. SPDX-License-Identifier: CC-BY-SA-4.0

Actions
^^^^^^^

FreedomBox's web front does not directly change any aspect of the underlying
operating system. Instead, it calls upon **actions**, as shell commands. Actions
live in ``/usr/share/plinth/actions`` directory. They require no interaction
beyond passing command line arguments or taking sensitive arguments via stdin.
They change the operation of the services and apps of the FreedomBox and nothing
else. These actions are also directly usable by a skilled administrator.

The following documentation for the ``actions`` module.

.. automodule:: plinth.actions
   :members: privileged
