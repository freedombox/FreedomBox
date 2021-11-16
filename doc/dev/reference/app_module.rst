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


<app-module>.is_essential
^^^^^^^^^^^^^^^^^^^^^^^^^

Optional. If an app must be installed and configured by FreedomBox without user
intervention, this attribute must be set to True. This attribute is part of the
:class:`~plinth.app.Info` component. Need for this attribute at the module level
will be removed in the future.

<app-module>.version
^^^^^^^^^^^^^^^^^^^^

Required. Version number of an app. Increasing the version number of an app
triggers the setup() logic allowing the app to run upgrade scripts. This
attribute is part of the :class:`~plinth.app.Info` component. Need for this
attribute at the module level will be removed in the future.

<app-module>.managed_services
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Optional. This must contain the list of all services that this app deals with.
This is mostly needed to enforce better security. This information is part of
the :class:`~plinth.daemon.Daemon` component. Need for this attribute at the
module level will be removed in the future.

<app-module>.managed_paths
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Optional. This must contain the list of all file system paths that this app
deals with. This is mostly used by the
:class:`~plinth.modules.letsencrypt.components.LetsEncrypt` component to enforce
better security. This requirement may be removed in the future.
