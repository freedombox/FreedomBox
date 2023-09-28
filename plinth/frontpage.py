# SPDX-License-Identifier: AGPL-3.0-or-later
"""Manage application shortcuts on front page."""

import json
import logging
import pathlib
from typing import ClassVar

from plinth import app, cfg
from plinth.modules.users import privileged as users_privileged

logger = logging.getLogger(__name__)


class Shortcut(app.FollowerComponent):
    """An application component for handling shortcuts."""

    _all_shortcuts: ClassVar[dict[str, 'Shortcut']] = {}

    def __init__(self, component_id, name, short_description=None, icon=None,
                 url=None, description=None, manual_page=None,
                 configure_url=None, clients=None, login_required=False,
                 allowed_groups=None):
        """Initialize the frontpage shortcut component for an app.

        When a user visits this web interface, they are first shown the
        frontpage. It's primary contents are the list of shortcuts to services
        that user may use on the server. If a service requires logging in, it
        does not show up to anonymous users. If a service requires a user to be
        part of a group, that service is only shown to those users.

        'component_id' must be a unique string across all apps and components
        of a app. Conventionally starts with 'shortcut-'.

        'name' is the mandatory title for the shortcut.

        'short_description' is an optional secondary title for the shortcut.

        'icon' is used to find a suitable image to represent the shortcut.

        'url' is link to which the user is redirected when the shortcut is
        activated. This is typically the web interface for a particular service
        provided by the app. For shortcuts that should simply additional
        information this value must be None.

        'description' is additional information that the user is shown when
        the shortcut is activated. This must be provided instead of 'url' and
        must be 'None' if 'url' is provided.

        'manual_page' is the optional name of the page for this app in the user
        manual. If provided, a 'Learn more...' link appears in the app page for
        this app.

        'configure_url' is the page to which the user may be redirected if they
        wish to change the settings for the app or one of its services. This is
        only used when 'url' is 'None'. It is optionally provided along with
        'description'.

        'clients' is a list of clients software that can used to access the
        service offered by the shortcut. This should be a valid client
        information structure as validated by clients.py:validate().

        If 'login_required' is true, only logged-in users will be shown this
        shortcut. Anonymous users visiting the frontpage won't be shown this
        shortcut.

        'allowed_groups' specifies a list of user groups to whom this shortcut
        must be shown. All other user groups will not be shown this shortcut on
        the frontpage. If 'login_required' is False, this property has not
        effect and the shortcut is shown to all the users including anonymous
        users.

        """
        super().__init__(component_id)

        if url is None:
            url = '?selected={id}'.format(id=component_id)

        self.name = name
        self.short_description = short_description
        self.url = url
        self.icon = icon
        self.description = description
        self.manual_page = manual_page
        self.configure_url = configure_url
        self.clients = clients
        self.login_required = login_required
        self.allowed_groups = set(allowed_groups) if allowed_groups else None

        self._all_shortcuts[self.component_id] = self

    def remove(self):
        """Remove this shortcut from global list of shortcuts."""
        del self._all_shortcuts[self.component_id]

    @classmethod
    def list(cls, username=None, web_apps_only=False, sort_by='name'):
        """Return menu items in sorted order according to current locale."""
        shortcuts_to_return = cls._list_for_user(username)
        if web_apps_only:
            shortcuts_to_return = {
                _id: shortcut
                for _id, shortcut in shortcuts_to_return.items()
                if not shortcut.url.startswith('?selected=')
            }

        return sorted(shortcuts_to_return.values(),
                      key=lambda item: getattr(item, sort_by).lower())

    @classmethod
    def _list_for_user(cls, username=None):
        """Return menu items for a particular user or anonymous user."""
        if not username:
            return cls._all_shortcuts

        # XXX: Turn this into an API call in users module and cache
        user_groups = set(users_privileged.get_user_groups(username))

        if 'admin' in user_groups:  # Admin has access to all services
            return cls._all_shortcuts

        shortcuts = {}
        for shortcut_id, shortcut in cls._all_shortcuts.items():
            if shortcut.login_required and shortcut.allowed_groups and \
               user_groups.isdisjoint(shortcut.allowed_groups):
                continue

            shortcuts[shortcut_id] = shortcut

        return shortcuts


def add_custom_shortcuts():
    custom_shortcuts = get_custom_shortcuts()

    for shortcut in custom_shortcuts['shortcuts']:
        web_app_url = _extract_web_app_url(shortcut)
        if not web_app_url:
            continue

        shortcut_id = shortcut.get('id', shortcut['name'])
        component_id = 'shortcut-custom-' + shortcut_id
        component = Shortcut(component_id, shortcut['name'],
                             shortcut['short_description'],
                             icon=shortcut['icon_url'], url=web_app_url)
        component.set_enabled(True)


def _extract_web_app_url(custom_shortcut):
    if not custom_shortcut.get('clients'):
        return None

    for client in custom_shortcut['clients']:
        if not client.get('platforms'):
            continue

        for platform in client['platforms']:
            if platform['type'] == 'web':
                return platform['url']

    return None


def get_custom_shortcuts_paths():
    """Return the list of custom shortcut file paths."""
    file_paths = [
        '/etc/freedombox/custom-shortcuts.json',
        '/etc/plinth/custom-shortcuts.json',
        '/var/lib/freedombox/custom-shortcuts.json',
        '/usr/share/freedombox/custom-shortcuts.json',
    ]
    return cfg.expand_to_dot_d_paths(file_paths)


def get_custom_shortcuts():
    """Return a merged dictionary of all custom shortcuts."""
    shortcuts = {'shortcuts': []}
    for file_path in get_custom_shortcuts_paths():
        file_path = pathlib.Path(file_path)
        try:
            if not file_path.is_file() or not file_path.stat().st_size:
                continue

            logger.info('Loading custom shortcuts from %s', file_path)
            with file_path.open(encoding='utf-8') as file_handle:
                shortcuts['shortcuts'] += json.load(file_handle)['shortcuts']
        except Exception as exception:
            logger.warning('Error loading shortcuts from %s: %s', file_path,
                           exception)

    return shortcuts
