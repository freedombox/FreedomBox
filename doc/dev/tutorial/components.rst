.. SPDX-License-Identifier: CC-BY-SA-4.0

Part 4: Components
------------------

Each :class:`~plinth.app.App` contains various :class:`~plinth.app.Component`
components that each provide one small functionality needed by the app. Each of
these components are instantiated and added to the app as children. The
:class:`~plinth.menu.Menu` object added in the previous step is one such
component.

Providing basic information about the app
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

We need to provide some basic information about the application for the app to
function normally.

.. code-block:: python3
  :caption: ``__init__.py``

  from django.utils.translation import gettext_lazy as _

  from plinth import app as app_module

  from . import manifest

  class TransmissionApp(app_module.App):
      ...

      def __init__(self):
        ...

        info = app_module.Info(app_id=self.app_id, version=1,
                               name=_('Transmission'),
                               icon_filename='transmission',
                               short_description=_('BitTorrent Web Client'),
                               description=description,
                               manual_page='Transmission',
                               clients=manifest.clients,
                               donation_url='https://transmissionbt.com/donate/')
        self.add(info)

The first argument is app_id that is same as the ID for the app. The version is
the version number for this app that must be incremented whenever setup() method
needs to be called again. name, icon_filename, short_description, description,
manual_page and clients provide information that is shown on the app's main
page. The donation_url encourages our users to contribute to upstream projects
in order ensure their long term sustainability. More information about the
parameters is available in :class:`~plinth.app.Info` class documentation.

The description of app should provide basic information on what the app is about
and how to use it. It is impractical, however, to explain everything about the
app in a few short paragraphs. So, we need to write a page about the app in the
FreedomBox manual. This page will be available to the users from within the
FreedomBox web interface. To make this happen, let us write a `manual page entry
<https://wiki.debian.org/FreedomBox/Manual/Transmission>`_ for our app in the
`FreedomBox Wiki <https://wiki.debian.org/FreedomBox/Manual>`_ and then provide
a link to it from app page.

It would be helpful to our users if we can show how they can use our app. If
there are desktop and mobile clients that can used to access our service, we
need to list them and present them. Let's add this information to
``manifest.py``.

.. code-block:: python3
  :caption: ``manifest.py``

  clients = [{
      'name': _('Transmission'),
      'platforms': [{
          'type': 'web',
          'url': '/transmission'
      }]
  }]

Since our app is a simple web application with no clients needed, we just list
that.

Managing a daemon
^^^^^^^^^^^^^^^^^

Transmission, like many services in the FreedomBox, requires a daemon to be
running in the system to work. When the app is enabled, the daemon should be
enabled. When the app is disabled, the daemon should be disabled. We should also
show the status of whether the daemon is running in the app's view. All of these
concerns are automatically handled by the framework if a
:class:`~plinth.daemon.Daemon` component is added to the app. Let us do that in
our app's class.

.. code-block:: python3
  :caption: ``__init__.py``

  from plinth.daemon import Daemon

  class TransmissionApp(app_module.App):
      ...

      def __init__(self):
        ...

        daemon = Daemon('daemon-transmission', 'transmission-daemon',
                        listen_ports=[(9091, 'tcp4')])
        self.add(daemon)


The first argument to instantiate the :class:`~plinth.daemon.Daemon` class is a
unique ID. The second is the name of the `systemd
<https://www.freedesktop.org/wiki/Software/systemd/>`_ unit file which manages
the daemon. The final argument is the list of ports that this daemon listens on.
This information is used to check if the daemon is listening on the expected
ports when the user requests diagnostic tests on the app.

Package management
^^^^^^^^^^^^^^^^^^

Transmission server is installed through a set of packages fetched from Debian
package repositories. The packages required for this are passed on to a
:class:`~plinth.package.Packages` component which takes care of installing,
upgrading and uninstalling the Debian packages. An app might require one or more
Debian packages to be installed.

.. code-block:: python3
  :caption: ``__init__.py``

  from plinth.package import Packages


  class TransmissionApp(app_module.App):
      ...

      def __init__(self):
        ...

        packages = Packages('packages-transmission', ['transmission-daemon'])
        self.add(packages)

The first argument uniquely identifies this instance of the `Packages`
component. Choose an appropriate unique identifier if your app has multiple
`Packages` components. The second argument is a list of Debian packages that
this component is responsible for.

Managing web server configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Transmission provides a web interface to the user. This web interface needs to
be proxied through a web server for security and access control. We will need to
write a configuration snippet for Apache, the default web server on FreedomBox.
This configuration snippet needs to be activated when our app is enabled. The
configuration snippet needs to be deactivated when our app is disabled. All of
these concerns are automatically handled by the framework if a
:class:`~plinth.modules.apache.components.Webserver` component is added to the
app. Let us do that in our app's class.

.. code-block:: python3
  :caption: ``__init__.py``

  from plinth.modules.apache.components import Webserver

  class TransmissionApp(app_module.App):
      ...

      def __init__(self):
        ...

        webserver = Webserver('webserver-transmission', 'transmission-plinth'
                              urls=['https://{host}/transmission'])
        self.add(webserver)

The first argument to instantiate the
:class:`~plinth.modules.apache.components.Webserver` class is a unique ID. The
second is the name of the Apache2 web server configuration snippet that contains
the directives to proxy Transmission web interface via Apache2. We then need to
create the configuration file itself in ``transmission-plinth.conf``. The
final argument is the list of URLs that the app exposes to the users of the app.
This information is used to check if the URLs are accessible as expected when
the user requests diagnostic tests on the app.

Simply creating and shipping a configuration file into ``/etc`` folder creates
some hassles. Consider the following scenario: a debian package, either
freedombox or the app's separate debian package ships a file in ``/etc``. Then
the user deliberately or accidentally modifies the configuration file. Then the
debian package provides a newer version of the configuration file with, say,
more tweaks. As a result, a configuration file prompt is shown to the user
during package upgrade process. In case of unattended upgrades, the package is
not upgraded at all. To avoid such problems, FreedomBox provides the
:class:`~plinth.config.DropinConfigs` component. Let us add it in our app's
class.

.. code-block:: python3
  :caption: ``__init__.py``

  from plinth.config import DropinConfigs

  class TransmissionApp(app_module.App):
      ...

      def __init__(self):
        ...

        dropin_configs = DropinConfigs('dropin-configs-transmission', [
            '/etc/apache2/conf-available/transmission-plinth.conf',
        ])
        self.add(dropin_configs)

The first argument to instantiate the :class:`~plinth.config.DropinConfigs`
class is the unique ID. The second argument is the list of configuration files
as paths is ``/etc/``. The :class:`~plinth.config.DropinConfigs` component
requires that a file be shipped into ``/usr/share/freedombox/etc`` instead of
``/etc``. The component will handle the creation of a symlink from ``/usr`` path
to ``/etc`` path. To ship the file, we can simply create file in the ``data/``
directory of the app and let the FreedomBox setup script handling the
installation and shipping.

.. code-block:: apache
  :caption: ``data/usr/share/freedombox/etc/apache2/conf-available/transmission-plinth.conf``

  ## On all sites, provide Transmission on a default path: /transmission
  <Location /transmission>
      ProxyPass        http://localhost:9091/transmission
  </Location>


Managing the firewall
^^^^^^^^^^^^^^^^^^^^^

FreedomBox has a tight firewall that closes off all TCP/UDP ports by default. If
a service needs to available to users on a port, it needs to open the ports in
firewalld, the default firewall configuration manager in FreedomBox. When the
app is enabled, the ports need to opened and when the app is disabled, the ports
needs to be closed. The FreedomBox framework again provides a component for
handling these operations. In case of our app, there is no need to open a
special port since the web ports are always kept open. However, it is still good
to specify that we operate on http/https ports so that users can be provided
this information along with additional information on whether the service is
available over Internet. Create the
:class:`~plinth.modules.firewall.components.Firewall` component during app
initialization.

.. code-block:: python3
  :caption: ``__init__.py``

  from plinth.modules.firewall.components import Firewall

  class TransmissionApp(app_module.App):
      ...

      def __init__(self):
        ...

        firewall = Firewall('firewall-transmission', name,
                            ports=['http', 'https'], is_external=True)
        self.add(firewall)

The first parameter is a unique ID. Second one is the name of the app that as
shown to the user in the firewall status page. Third argument is the list of
services known to firewalld as listed in ``/usr/lib/firewalld/services/``.
Custom services can also be written. The final argument decides whether the
service should be made available by FreedomBox from external networks,
essentially the Internet.

User authentication and authorization
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

We wish that only users of FreedomBox should access the web interface of our
app. Further, only users belonging to a specially created group are the only
ones who should be able access the app. Again, FreedomBox handles all of this
and we simply need to declare and use. First we need to register a user group
with the FreedomBox framework in ``__init.py__``.

.. code-block:: python3
  :caption: ``__init__.py``

  from plinth.modules.users.components import UsersAndGroups

  class TransmissionApp(app_module.App):
      ...

      def __init__(self):
          ...

          groups = { 'bit-torrent': _('Download files using BitTorrent applications') }
          users_and_groups = UsersAndGroups('users-and-groups-transmission',
                                            groups=groups)
          self.add(users_and_groups)


Then in the Apache configuration snippet, we can mandate that only users of this
group (and, of course, admin users) should be allowed to access our app. In the
file ``transmission-plinth.conf``, add the following.

.. code-block:: apache
  :caption: ``data/etc/apache2/conf-available/transmission-plinth.conf``

  <Location /transmission>
      ...
      Include          includes/freedombox-single-sign-on.conf
      <IfModule mod_auth_pubtkt.c>
          TKTAuthToken "admin" "bit-torrent"
      </IfModule>
  </Location>

Showing a shortcut in the front page
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The app view we have created is only accessible by administrators of FreedomBox
since only they can configure the app. Other users who have access to this app
should have a way of discovering the app. This is done by providing a link in
the front page of FreedomBox web interface. This is the page that user's see
when they visit FreedomBox. To provide this shortcut, a
:class:`~plinth.frontpage.Shortcut` component can added to the app.

.. code-block:: python3
  :caption: ``__init__.py``

  from plinth import frontpage

  group = ('bit-torrent', 'Download files using BitTorrent applications')

  class TransmissionApp(app_module.App):
      ...

      def __init__(self):
          ...

          shortcut = frontpage.Shortcut(
              'shortcut-transmission', name, short_description=short_description,
              icon='transmission', url='/transmission', clients=clients,
              login_required=True, allowed_groups=[group[0]])
          self.add(shortcut)

The first parameter, as usual, is a unique ID. The next three parameters are
basic information about the app similar to the menu item. The URL parameter
specifies the URL that the user should be directed to when the shortcut is
clicked. This is the web interface provided by our app. The next parameter
provides a list of clients. This is useful for the FreedomBox mobile app when
the information is used to suggest installing mobile apps. This is described in
a later section of this tutorial. The next parameter specifies whether anonymous
users who are not logged into FreedomBox should be shown this shortcut. The
final parameter further restricts to which group of users this shortcut must be
shown.

Adding backup/restore functionality
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Each app in FreedomBox needs to provide the ability to backup and restore its
configuration and data. Apart from providing durability to users' data, this
allows the user to migrate from one machine to another. FreedomBox framework
provides a component for handling these operations. Create the
:class:`~plinth.modules.backups.components.BackupRestore` component during app
initialization.

In ``__init__.py``, add:

.. code-block:: python3
  :caption: ``__init__.py``

  from plinth.modules.backups.components import BackupRestore

  from . import manifest

  class TransmissionApp(app_module.App):
    ...

    def __init__(self):
        ...

        backup_restore = BackupRestore('backup-restore-transmission',
                                       **manifest.backup)
        self.add(backup_restore)

In ``manifest.py``, add:

.. code-block:: python3
  :caption: ``manifest.py``

  backup = {
      'data': {
          'directories': ['/var/lib/transmission-daemon/.config']
      },
      'secrets': {
          'files': ['/etc/transmission-daemon/settings.json']
      },
      'services': ['transmission-daemon']
  }

The data and secrets information specifies which list of files and directories
FreedomBox framework needs to backup and restore. The list of services specifies
which daemons should be stopped during the backup and restore process.
