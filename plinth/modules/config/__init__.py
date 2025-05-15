# SPDX-License-Identifier: AGPL-3.0-or-later
"""FreedomBox app for basic system configuration."""

import pathlib

import augeas
from django.utils.translation import gettext_lazy as _

from plinth import app as app_module
from plinth import frontpage, menu
from plinth.daemon import RelatedDaemon
from plinth.modules.apache import (get_users_with_website, user_of_uws_url,
                                   uws_url_of_user)
from plinth.package import Packages
from plinth.privileged import service as service_privileged

from . import manifest, privileged

_description = [
    _('Here you can set some general configuration options '
      'like webserver home page etc.')
]

ADVANCED_MODE_KEY = 'advanced_mode'


class ConfigApp(app_module.App):
    """FreedomBox app for basic system configuration."""

    app_id = 'config'

    _version = 6

    can_be_disabled = False

    def __init__(self) -> None:
        """Create components for the app."""
        super().__init__()
        info = app_module.Info(app_id=self.app_id, version=self._version,
                               is_essential=True,
                               depends=['apache', 'firewall', 'names'
                                        ], name=_('General Configuration'),
                               icon='fa-cog', description=_description,
                               manual_page='Configure', tags=manifest.tags)
        self.add(info)

        menu_item = menu.Menu('menu-config', _('Configure'), info.icon,
                              info.tags, 'config:index',
                              parent_url_name='system:system', order=30)
        self.add(menu_item)

        packages = Packages('packages-config', ['zram-tools'])
        self.add(packages)

        daemon1 = RelatedDaemon('related-daemon-config1', 'systemd-journald')
        self.add(daemon1)

        daemon2 = RelatedDaemon('related-daemon-config2', 'rsyslog')
        self.add(daemon2)

    def setup(self, old_version):
        """Install and configure the app."""
        super().setup(old_version)

        if old_version <= 3:
            privileged.set_logging_mode('volatile')
        elif old_version == 4:
            privileged.set_logging_mode(privileged.get_logging_mode())

        if old_version <= 5:
            # Update the style of Apache home page redirection.
            home_page = get_home_page()
            if home_page == 'apache-default':
                change_home_page(home_page)

        # systemd-journald is socket activated, it may not be running and it
        # does not support reload.
        service_privileged.try_restart('systemd-journald')
        # rsyslog when enabled, is activated by syslog.socket (shipped by
        # systemd). See:
        # https://www.freedesktop.org/wiki/Software/systemd/syslog/ .
        service_privileged.disable('rsyslog')
        # Ensure that rsyslog is not started by something else as it is
        # installed by default on Debian systems.
        service_privileged.mask('rsyslog')


def home_page_url2scid(url: str | None):
    """Return the shortcut ID of the given home page url."""
    # url is None when the freedombox-apache-homepage configuration file exists
    # but is empty. In this case, no redirect is effective.
    if url in ('/index.html', None):
        return 'apache-default'

    if url in ('/plinth/', '/plinth', 'plinth', '/freedombox/', '/freedombox',
               'freedombox'):
        return 'plinth'

    if url and url.startswith('/~'):
        return 'uws-{}'.format(user_of_uws_url(url))

    shortcuts = frontpage.Shortcut.list()
    for shortcut in shortcuts:
        if shortcut.url == url:
            return shortcut.component_id

    return None


def _home_page_scid2url(shortcut_id: str) -> str | None:
    """Return the url for the given home page shortcut ID."""
    if shortcut_id == 'plinth':
        url = '/plinth/'
    elif shortcut_id == 'apache-default':
        url = None
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


def _get_home_page_url() -> str | None:
    """Get the default application for the domain."""
    conf_file = privileged.APACHE_HOMEPAGE_CONFIG
    if not pathlib.Path(conf_file).exists():
        return '/plinth/'

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
    url = _get_home_page_url()
    return home_page_url2scid(url)


def change_home_page(shortcut_id: str):
    """Change the FreedomBox's default redirect to URL of a shortcut."""
    url = _home_page_scid2url(shortcut_id)
    if url:
        url = str(url)

    # URL may be a reverse_lazy() proxy
    privileged.set_home_page(url)


def get_advanced_mode():
    """Get whether option is enabled."""
    from plinth import kvstore
    return kvstore.get_default(ADVANCED_MODE_KEY, False)


def set_advanced_mode(advanced_mode):
    """Turn on/off advanced mode."""
    from plinth import kvstore
    kvstore.set(ADVANCED_MODE_KEY, advanced_mode)
