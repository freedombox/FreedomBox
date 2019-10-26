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

<app-module>.diagnose()
^^^^^^^^^^^^^^^^^^^^^^^

Optional. Called when the user invokes system-wide diagnostics by visiting
**System -> Diagnositcs**. This method must return an array of diagnostic
results. Each diagnostic result must be a two-tuple with first element as a
string that is shown to the user as name of the test and second element is the
result of the test. It must be one of ``passed``, ``failed``, ``error``. Example
return value:

.. code-block:: python3

  [('Check http://localhost/app is reachable', 'passed'),
   ('Check configuration is sane', 'passed')]

<app-module>.depends
^^^^^^^^^^^^^^^^^^^^

Optional. This module property must contain a list of all apps that this
application depends on. The application is specified as string containing the
full module load path. For example, ``names``.
