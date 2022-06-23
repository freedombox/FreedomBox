.. SPDX-License-Identifier: CC-BY-SA-4.0

Part 6: Setup
-------------

Installing packages required for the app
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

So far, we haven't dealt with installing the packages needed for Transmission to
work. Nor did we take care of performing the initial configuration for
Transmission. FreedomBox takes care of installing all the Debian packages
required for our app to work. All we need to do is specify the list of the
Debian packages required in the ``setup()`` method that is called during
installation:

.. code-block:: python3
  :caption: ``__init__.py``

  def setup(helper, old_version=None):
      """Install and configure the module."""
      app.setup(old_version)

      new_configuration = {
          'rpc-whitelist-enabled': False,
          'rpc-authentication-required': False
      }
      helper.call('post', privileged.merge_configuration, new_configuration)
      helper.call('post', app.enable)

The first time this app's view is accessed, FreedomBox shows an app installation
page and allows the user to install the app. After the app installation is
completed, the user is shown the app's configuration page.

In case of our app Transmission, first we are installing the Debian packages,
then performing the first time configuration on the app using the action script
and finally enabling the app.
