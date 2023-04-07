# SPDX-License-Identifier: AGPL-3.0-or-later
"""Configure sharing."""

import os
import pathlib
import re

import augeas

from plinth import action_utils
from plinth.actions import privileged

APACHE_CONFIGURATION = '/etc/apache2/conf-available/sharing-freedombox.conf'


@privileged
def setup():
    """Create an empty apache configuration file."""
    path = pathlib.Path(APACHE_CONFIGURATION)
    if not path.exists():
        path.touch()


def load_augeas():
    """Initialize augeas for this app's configuration file."""
    aug = augeas.Augeas(flags=augeas.Augeas.NO_LOAD +
                        augeas.Augeas.NO_MODL_AUTOLOAD)
    aug.set('/augeas/load/Httpd/lens', 'Httpd.lns')
    aug.set('/augeas/load/Httpd/incl[last() + 1]', APACHE_CONFIGURATION)
    aug.load()

    aug.defvar('conf', '/files' + APACHE_CONFIGURATION)

    return aug


@privileged
def add(name: str, path: str, groups: list[str], is_public: bool):
    """Add a share to Apache configuration."""
    path = '"' + path.replace('"', r'\"') + '"'
    url = '/share/' + name

    if not os.path.exists(APACHE_CONFIGURATION):
        pathlib.Path(APACHE_CONFIGURATION).touch()

    aug = load_augeas()
    shares = _list(aug)
    if any([share for share in shares if share['name'] == name]):
        raise Exception('Share already present')

    aug.set('$conf/directive[last() + 1]', 'Alias')
    aug.set('$conf/directive[last()]/arg[1]', url)
    aug.set('$conf/directive[last()]/arg[2]', path)

    aug.set('$conf/Location[last() + 1]/arg', url)

    aug.set('$conf/Location[last()]/directive[last() + 1]', 'Include')
    aug.set('$conf/Location[last()]/directive[last()]/arg',
            'includes/freedombox-sharing.conf')

    if not is_public:
        aug.set('$conf/Location[last()]/directive[last() + 1]', 'Include')
        aug.set('$conf/Location[last()]/directive[last()]/arg',
                'includes/freedombox-single-sign-on.conf')

        aug.set('$conf/Location[last()]/IfModule/arg', 'mod_auth_pubtkt.c')
        aug.set('$conf/Location[last()]/IfModule/directive[1]', 'TKTAuthToken')
        for group_name in groups:
            aug.set(
                '$conf/Location[last()]/IfModule/directive[1]/arg[last() + 1]',
                group_name)
    else:
        aug.set('$conf/Location[last()]/directive[last() + 1]', 'Require')
        aug.set('$conf/Location[last()]/directive[last()]/arg[1]', 'all')
        aug.set('$conf/Location[last()]/directive[last()]/arg[2]', 'granted')

    aug.save()

    with action_utils.WebserverChange() as webserver_change:
        webserver_change.enable('sharing-freedombox')


@privileged
def remove(name: str):
    """Remove a share from Apache configuration."""
    url_to_remove = '/share/' + name

    aug = load_augeas()

    for directive in aug.match('$conf/directive'):
        if aug.get(directive) != 'Alias':
            continue

        url = aug.get(directive + '/arg[1]')
        if url == url_to_remove:
            aug.remove(directive)

    for location in aug.match('$conf/Location'):
        url = aug.get(location + '/arg')
        if url == url_to_remove:
            aug.remove(location)

    aug.save()

    with action_utils.WebserverChange() as webserver_change:
        webserver_change.enable('sharing-freedombox')


def _get_name_from_url(url):
    """Return the name of the share given the URL for it."""
    matches = re.match(r'/share/([a-z0-9\-]*)', url)
    if not matches:
        raise ValueError

    return matches[1]


def _list(aug=None):
    """List all Apache configuration shares."""
    if not aug:
        aug = load_augeas()

    shares = []

    for match in aug.match('$conf/directive'):
        if aug.get(match) != 'Alias':
            continue

        url = aug.get(match + '/arg[1]')
        path = aug.get(match + '/arg[2]')

        path = path.removesuffix('"').removeprefix('"')
        path = path.replace(r'\"', '"')
        try:
            name = _get_name_from_url(url)
            shares.append({
                'name': name,
                'path': path,
                'url': '/share/' + name
            })
        except ValueError:
            continue

    for location in aug.match('$conf/Location'):
        url = aug.get(location + '/arg')

        try:
            name = _get_name_from_url(url)
        except ValueError:
            continue

        groups = []
        for group in aug.match(location + '//directive["TKTAuthToken"]/arg'):
            groups.append(aug.get(group))

        def _is_public():
            """Must contain the line 'Require all granted'."""
            require = location + '//directive["Require"]'
            return bool(aug.match(require)) and aug.get(
                require +
                '/arg[1]') == 'all' and aug.get(require +
                                                '/arg[2]') == 'granted'

        for share in shares:
            if share['name'] == name:
                share['groups'] = groups
                share['is_public'] = _is_public()

    return shares


@privileged
def list_shares() -> list[dict[str, object]]:
    """List all Apache configuration shares and print as JSON."""
    return _list()


@privileged
def uninstall():
    """Remove apache config when app is uninstalled."""
    pathlib.Path(APACHE_CONFIGURATION).unlink(missing_ok=True)
