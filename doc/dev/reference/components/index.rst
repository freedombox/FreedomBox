.. SPDX-License-Identifier: CC-BY-SA-4.0

Components
----------

.. toctree::
   :caption: Available components:

   info
   enablestate
   menu
   packages
   config
   daemon
   firewall
   webserver
   frontpage
   domain
   letsencrypt
   users
   staticfiles
   backups
   coturn

Base Classes
^^^^^^^^^^^^

.. autoclass:: plinth.app.Component
   :members:

.. autoclass:: plinth.app.LeaderComponent
   :members:

.. autoclass:: plinth.app.FollowerComponent
   :members:

Other Classes
^^^^^^^^^^^^^

.. autoclass:: plinth.modules.diagnostics.check.DiagnosticCheck
   :members:

.. autoclass:: plinth.modules.diagnostics.check.Result
   :members:
