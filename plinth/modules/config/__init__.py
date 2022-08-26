# SPDX-License-Identifier: AGPL-3.0-or-later
"""FreedomBox app for basic system configuration."""

import socket

import augeas
from django.utils.translation import gettext_lazy as _

from plinth import app as app_module
from plinth import frontpage, menu
from plinth.daemon import RelatedDaemon
from plinth.modules.apache import (get_users_with_website, user_of_uws_url,
                                   uws_url_of_user)
from plinth.modules.names.components import DomainType
from plinth.package import Packages
from plinth.signals import domain_added

from . import privileged

_description = [
    _('Here you can set some general configuration options '
      'like hostname, domain name, webserver home page etc.')
]

ADVANCED_MODE_KEY = 'advanced_mode'


class ConfigApp(app_module.App):
    """FreedomBox app for basic system configuration."""

    app_id = 'config'

    _version = 4

    can_be_disabled = False

    def __init__(self):
        """Create components for the app."""
        super().__init__()
        info = app_module.Info(app_id=self.app_id, version=self._version,
                               is_essential=True,
                               depends=['apache', 'firewall', 'names'
                                        ], name=_('General Configuration'),
                               icon='fa-cog', description=_description,
                               manual_page='Configure')
        self.add(info)

        menu_item = menu.Menu('menu-config', _('Configure'), None, info.icon,
                              'config:index', parent_url_name='system')
        self.add(menu_item)

        packages = Packages('packages-config', ['zram-tools'])
        self.add(packages)

        daemon1 = RelatedDaemon('related-daemon-config1', 'systemd-journald')
        self.add(daemon1)

        daemon2 = RelatedDaemon('related-daemon-config2', 'rsyslog')
        self.add(daemon2)

        domain_type = DomainType('domain-type-static', _('Domain Name'),
                                 'config:index', can_have_certificate=True)
        self.add(domain_type)

    @staticmethod
    def post_init():
        """Perform post initialization operations."""
        # Register domain with Name Services module.
        domainname = get_domainname()
        if domainname:
            domain_added.send_robust(sender='config',
                                     domain_type='domain-type-static',
                                     name=domainname, services='__all__')

    def setup(self, old_version):
        """Install and configure the app."""
        super().setup(old_version)
        _migrate_home_page_config()

        if old_version <= 3:
            privileged.set_logging_mode('volatile')

        # systemd-journald is socket activated, it may not be running and it
        # does not support reload.
        actions.superuser_run('service', ['try-restart', 'systemd-journald'])
        # rsyslog when enabled, is activated by syslog.socket (shipped by
        # systemd). See:
        # https://www.freedesktop.org/wiki/Software/systemd/syslog/ .
        actions.superuser_run('service', ['disable', 'rsyslog'])
        # Ensure that rsyslog is not started by something else as it is
        # installed by default on Debian systems.
        actions.superuser_run('service', ['mask', 'rsyslog'])


def get_domainname():
    """Return the domainname."""
    fqdn = socket.getfqdn()
    return '.'.join(fqdn.split('.')[1:])


def get_hostname():
    """Return the hostname."""
    return socket.gethostname()


def home_page_url2scid(url):
    """Return the shortcut ID of the given home page url."""
    if url in ('/plinth/', '/plinth', 'plinth'):
        return 'plinth'

    if url == '/index.html':
        return 'apache-default'

    if url and url.startswith('/~'):
        return 'uws-{}'.format(user_of_uws_url(url))

    shortcuts = frontpage.Shortcut.list()
    for shortcut in shortcuts:
        if shortcut.url == url:
            return shortcut.component_id

    return None


def _home_page_scid2url(shortcut_id):
    """Return the url for the given home page shortcut ID."""
    if shortcut_id is None:
        url = None
    elif shortcut_id == 'plinth':
        url = '/plinth/'
    elif shortcut_id == 'apache-default':
        url = '/index.html'
    elif shortcut_id.startswith('uws-'):
        user = shortcut_id[4:]
        if user in get_users_with_website():
            url = uws_url_of_user(user)
        else:
            url = None
    else:
        shortcuts = frontpage.Shortcut.list()
        aux = [
            shortcut.url for shortcut in shortcuts
            if shortcut_id == shortcut.component_id
        ]
        url = aux[0] if 1 == len(aux) else None

    return url


def _get_home_page_url(conf_file):
    """Get the default application for the domain."""
    aug = augeas.Augeas(flags=augeas.Augeas.NO_LOAD +
                        augeas.Augeas.NO_MODL_AUTOLOAD)
    aug.set('/augeas/load/Httpd/lens', 'Httpd.lns')
    aug.set('/augeas/load/Httpd/incl[last() + 1]', conf_file)
    aug.load()

    aug.defvar('conf', '/files' + conf_file)

    for match in aug.match('/files' + conf_file +
                           '/directive["RedirectMatch"]'):
        if aug.get(match + "/arg[1]") == '''"^/$"''':
            return aug.get(match + "/arg[2]").strip('"')

    return None


def get_home_page():
    """Return the shortcut ID that is set as current home page."""
    CONF_FILE = privileged.APACHE_HOMEPAGE_CONFIG if os.path.exists(
        privileged.APACHE_HOMEPAGE_CONFIG
    ) else privileged.FREEDOMBOX_APACHE_CONFIG

    url = _get_home_page_url(CONF_FILE)
    return home_page_url2scid(url)


def change_home_page(shortcut_id):
    """Change the FreedomBox's default redirect to URL of a shortcut."""
    url = _home_page_scid2url(shortcut_id)
    if url is None:
        url = '/plinth/'  # fall back to default url if scid is unknown.

    # URL may be a reverse_lazy() proxy
    privileged.set_home_page(str(url))


def get_advanced_mode():
    """Get whether option is enabled."""
    from plinth import kvstore
    return kvstore.get_default(ADVANCED_MODE_KEY, False)


def set_advanced_mode(advanced_mode):
    """Turn on/off advanced mode."""
    from plinth import kvstore
    kvstore.set(ADVANCED_MODE_KEY, advanced_mode)


def _migrate_home_page_config():
    """Move the home page configuration to an external file."""
    # Hold the current home page in a variable
    home_page = get_home_page()

    # Reset the home page to plinth in freedombox.conf
    privileged.reset_home_page()

    # Write the home page setting into the new conf file
    # This step is run at the end because it reloads the Apache server
    change_home_page(home_page)
