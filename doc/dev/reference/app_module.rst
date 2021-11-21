.. SPDX-License-Identifier: CC-BY-SA-4.0

App Module
----------

These methods are optionally provided by the module in which an app is
implemented and FreedomBox calls/uses them if they are present.

<app-module>.depends
^^^^^^^^^^^^^^^^^^^^

Optional. This module property must contain a list of all apps that this
application depends on. The application is specified as string which is the
final part of the full module load path. For example, ``names``. Dependencies
are part of the :class:`~plinth.app.Info` component. Need for this attribute at
the module level will be removed in the future.
