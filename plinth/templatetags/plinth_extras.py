# SPDX-License-Identifier: AGPL-3.0-or-later

import os
from urllib.parse import urlparse

from django import template

from plinth import clients as clients_module

register = template.Library()


def mark_active_menuitem(menu, path):
    """Mark the best-matching menu item with 'active'

    Input: a menu dict in the form of:
        [{'url': '/path/to/choice1/', 'text': 'choice 1'}, {'url': ...}]

    URL paths are expected to end with a slash for matches to work properly.

    Output: The same dictionary; the best-matching URL dict gets the value
    'active': True. All other URL dicts get the value 'active': False.

    Note: this sets the 'active' values on the menu itself, not on a copy.
    """
    best_match = ''
    best_match_item = None

    for urlitem in menu:
        urlitem['active'] = False
        if not path.startswith(str(urlitem['url'])):
            continue

        match = os.path.commonprefix([str(urlitem['url']), path])
        if len(match) > len(best_match):
            best_match = match
            best_match_item = urlitem

    if best_match_item:
        best_match_item['active'] = True

    return menu


@register.inclusion_tag('subsubmenu.html', takes_context=True)
def show_subsubmenu(context, menu):
    """Mark the active menu item and display the subsubmenu"""
    menu = mark_active_menuitem(menu, context['request'].path)
    return {'subsubmenu': menu}


@register.filter(name='clients_of_type')
def clients_of_type(clients, client_type):
    """Filter and get clients of a particular type"""
    return clients_module.of_type(clients, client_type)


@register.filter(name='lookup')
def lookup(dictionary, key):
    """Get the value in the dictionary at given key"""
    return dictionary[key]


def _is_internal_url(url):
    """Check if the given link is internal or not.

    A URL is internal if it is relative URL or points to one of the domains
    managed by FreedomBox.
    """
    parsed_url = urlparse(str(url))
    if not parsed_url.netloc:
        return True

    from plinth.modules.names.components import DomainName
    return parsed_url.netloc in DomainName.list_names()


@register.filter(name='clients_get_platforms')
def clients_get_platforms(clients):
    """Return lists of self hosted platforms and all other platforms."""
    other = []
    web = []
    for client in clients:
        for platform in client['platforms']:
            if platform['type'] == 'web' and _is_internal_url(platform['url']):
                web.append(platform)
            else:
                other.append(platform)

    return {'web': web, 'other': other}
