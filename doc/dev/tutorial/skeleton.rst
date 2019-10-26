.. SPDX-License-Identifier: CC-BY-SA-4.0

Part 2: Skeleton
----------------

Let us get started with creating our FreedomBox app.

Creating the project structure
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Create a directory structure as follows with empty files. We will fill them up
in a step-by-step manner::

   ─┬ <plinth_root>/
    ├─┬ plinth/
    │ └─┬ modules/
    │   └─┬ transmission/
    │     ├─ __init__.py
    │     ├─ forms.py
    │     ├─ manifest.py
    │     ├─ urls.py
    │     ├─ views.py
    │     ├─┬ data/
    │     │ └─┬ etc/
    │     │   ├─┬ plinth/
    │     │   │ └─┬ modules-enabled/
    │     │   │   └─ transmission
    │     │   └─┬ apache2/
    │     │     └─┬ conf-available/
    │     │       └─ transmission-freedombox.conf
    │     └─┬ tests
    │       └─ __init__.py
    └─┬ actions/
      └─ transmission

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
``plinth/modules/transmission/data/etc/plinth/modules-enabled/``. Let us create
this file ``transmission``::

  plinth.modules.transmission

This file is automatically installed to ``/etc/plinth/modules-enabled/`` by
FreedomBox's installation script ``setup.py``. If we are writing a module that
resides independently outside the FreedomBox's source code, the setup script
will need to copy it to the target location. Further, it is not necessary for
the app to be part of the ``plinth.modules`` namespace. It can, for example, be
``freedombox_transmission``.

Creating the App class
^^^^^^^^^^^^^^^^^^^^^^

In the FreedomBox framework, each app must be a class derived from the
:class:`plinth.app.App`. Let us to that in ``__init__.py``. We will fill up the
class later.

.. code-block:: python3

  from plinth import app as app_module

  class TransmissionApp(app_module.App):
      """FreedomBox app for Transmission."""

      app_id = 'transmission'

      def __init__(self):
          """Create components for the app."""
          super().__init__()

As soon as FreedomBox Service (Plinth) starts, it will load all the enabled
modules. After this, it gives a chance to each of the modules to initialize
itself by calling the ``init()`` method if there is such a method available as
``<module>.init()``. The app class must be instantiated here.

.. code-block:: python3

  app = None

  def init():
      """Initialize the Transmission module."""
      global app
      app = TransmissionApp()

      setup_helper = globals()['setup_helper']
      if setup_helper.get_state() != 'needs-setup' and app.is_enabled():
          app.set_enabled(True)
