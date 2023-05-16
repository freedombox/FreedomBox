.. SPDX-License-Identifier: CC-BY-SA-4.0

Part 2: Skeleton
----------------

Let us get started with creating our FreedomBox app.

Creating the project structure
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Create a directory structure as follows with empty files. We will fill them up
in a step-by-step manner::

   ─┬ <plinth_root>/
    └─┬ plinth/
      └─┬ modules/
        └─┬ transmission/
          ├─ __init__.py
          ├─ forms.py
          ├─ privileged.py
          ├─ manifest.py
          ├─ urls.py
          ├─ views.py
          ├─┬ data/
          │ ├─┬ usr/
          │ │ └─┬ share/
          │ │   └─┬ freedombox/
          │ │     └─┬ etc/
          │ │       └─┬ apache2/
          │ │         └─┬ conf-available/
          │ │           └─ transmission-plinth.conf
          │ └─┬ usr/
          │   └─┬ share/
          │     └─┬ freedombox/
          │       └─┬ modules-enabled/
          │         └─ transmission
          └─┬ tests
            └─ __init__.py

The file ``__init__.py`` indicates that the directory in which it is present is
a Python module. For now, it is an empty file.

FreedomBox's setup script ``setup.py`` will automatically install the
``plinth/modules/transmission`` directory (along with other files described
later) to an appropriate location. If you are creating an app that stays
independent and outside of FreedomBox source tree, then ``setup.py`` script in
your source tree will need to install it to a proper location on the system. The
``plinth/modules/`` directory is a Python3 `namespace package
<https://www.python.org/dev/peps/pep-0420/>`_. So, you can install it with the
``plinth/modules/`` directory structure into any Python path and still be
discovered as ``plinth.modules.*``.

Tell FreedomBox that our app exists
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The first thing to do is tell FreedomBox that our app exists. This is done by
writing a small file with the Python import path to our app and placing it in
``plinth/modules/transmission/data/usr/share/freedombox/modules-enabled/``. Let
us create this file ``transmission``:

.. code-block:: text
  :caption: ``plinth/modules/transmission/data/usr/share/freedombox/modules-enabled/transmission``

  plinth.modules.transmission

This file is automatically installed to
``/usr/share/freedombox/modules-enabled/`` by FreedomBox's installation script
``setup.py``. If we are writing a module that resides independently outside the
FreedomBox's source code, the setup script will need to copy it to the target
location. Further, it is not necessary for the app to be part of the
``plinth.modules`` namespace. It can, for example, be
``freedombox_transmission``.

Creating the App class
^^^^^^^^^^^^^^^^^^^^^^

In the FreedomBox framework, each app must be a class derived from the
:class:`plinth.app.App`. Let us do that in ``__init__.py``. We will fill up the
class later.

.. code-block:: python3
  :caption: ``__init__.py``

  from plinth import app as app_module

  class TransmissionApp(app_module.App):
      """FreedomBox app for Transmission."""

      app_id = 'transmission'

      def __init__(self):
          """Create components for the app."""
          super().__init__()

As soon as FreedomBox Service (Plinth) starts, it will load all the enabled
modules and create app instances for App classes in the module.
