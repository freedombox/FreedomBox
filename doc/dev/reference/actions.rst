.. SPDX-License-Identifier: CC-BY-SA-4.0

Privileged Actions
^^^^^^^^^^^^^^^^^^

FreedomBox Service performs most changes to the underlying operating system
using remote calls into the **freedombox-privileged** daemon or other daemons
such as NetworkManager and UDisks.

The following documentation for the ``actions`` module which contains function
decorators to mark a method to run with privileged permissions.

.. automodule:: freedombox.actions
   :members: privileged
