.. SPDX-License-Identifier: CC-BY-SA-4.0

Part 6: Setup
-------------

Installing packages required for the app
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

So far, we haven't dealt with installing the packages needed for Transmission to
work. Nor did we take care of performing the initial configuration for
Transmission. FreedomBox takes care of installing all the Debian packages
required for our app to work. All we need to do is call the base class method in
the ``setup()`` method that of the ``TrasmissionApp`` class that is called
during installation. The base class ``setup()`` method in turn calls ``setup()``
on the ``Packages`` component which performs the actual installation:

.. code-block:: python3
  :caption: ``__init__.py``

  class TransmissionApp(app_module.App):
      ...

      def setup(self, old_version):
          """Install and configure the app."""
          super().setup(old_version)

          new_configuration = {
              'rpc-whitelist-enabled': False,
              'rpc-authentication-required': False
          }
          privileged.merge_configuration(new_configuration)

          self.enable()

The first time this app's view is accessed, FreedomBox shows an app installation
page and allows the user to install the app. After the app installation is
completed, the user is shown the app's configuration page.

In case of our app Transmission, first we are installing the Debian packages (by
calling base class ``setup()`` method), then performing the first time
configuration on the app using the action script and finally enabling the app.
