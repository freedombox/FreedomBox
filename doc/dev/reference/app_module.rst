.. SPDX-License-Identifier: CC-BY-SA-4.0

App Module
----------

These methods are optionally provided by the module in which an app is
implemented and FreedomBox calls/uses them if they are present.

<app-module>.init()
^^^^^^^^^^^^^^^^^^^

Optional. This method is called by FreedomBox soon after all the applications
are loaded. The ``init()`` call order guarantees that other applications that
this application depends on will be initialized before this application is
initialized.

<app-module>.depends
^^^^^^^^^^^^^^^^^^^^

Optional. This module property must contain a list of all apps that this
application depends on. The application is specified as string containing the
full module load path. For example, ``names``.
