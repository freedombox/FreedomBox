#
# This file is part of Plinth.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import os
from enum import Enum

from django import template

register = template.Library()


class Desktop_OS(Enum):
    GNU_LINUX = 'gnu-linux'
    MAC_OS = 'mac-os'
    WINDOWS = 'windows'


class Mobile_OS(Enum):
    ANDROID = 'android'
    IOS = 'ios'


class Store(Enum):
    APP_STORE = 'app-store'
    F_DROID = 'f-droid'
    GOOGLE_PLAY = 'google-play'


def enum_values(enum):
    return [x.value for x in list(enum)]


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


def __check(clients, cond):
    """Check if any of a list of clients satisfies the given condition"""
    clients = clients if isinstance(clients, list) else [clients]
    return any(pf for client in clients for pf in client['platforms']
               if cond(pf))


@register.filter(name='has_desktop_clients')
def has_desktop_clients(clients):
    """Filter to find out whether an application has desktop clients"""
    return __check(clients,
                   lambda x: x.get('os', '') in enum_values(Desktop_OS))


@register.filter(name='has_mobile_clients')
def has_mobile_clients(clients):
    """Filter to find out whether an application has mobile clients"""
    return __check(clients,
                   lambda x: x.get('os', '') in enum_values(Mobile_OS))


@register.filter(name='has_web_clients')
def has_web_clients(clients):
    """Filter to find out whether an application has web clients"""
    return __check(clients, lambda x: x['type'] == 'web')


@register.filter(name='has_package_clients')
def has_package_clients(clients):
    """Filter to find out whether an application has web clients"""
    return __check(clients, lambda x: x['type'] == 'package')


@register.filter(name='of_type')
def of_type(clients, typ):
    """Filter and get clients of a particular type"""
    filters = {
        'mobile': has_mobile_clients,
        'desktop': has_desktop_clients,
        'web': has_web_clients,
        'package': has_package_clients,
    }
    return list(filter(filters.get(typ, lambda x: x), clients))
