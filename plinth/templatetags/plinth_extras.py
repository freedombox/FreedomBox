#
# This file is part of FreedomBox.
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


@register.filter(name='is_relative_url')
def is_relative_url(url):
    """Check if the given link is relative or not"""
    parsed_url = urlparse(url)
    return not parsed_url.netloc


@register.filter(name='get_self_hosted_web_apps')
def get_self_hosted_web_apps(clients):
    """Get a list of self hosted web apps"""
    clients_with_web_platforms = list(
        filter(
            lambda c: len(
                list(filter(lambda p: p['type'] == 'web', c['platforms']))),
            clients))
    clients_with_self_hosted_apps = list(
        filter(
            lambda c: len(
                list(
                    filter(lambda p: is_relative_url(p['url']), c['platforms'])
                )), clients_with_web_platforms))
    mapped_list = list(
        map(
            lambda c: list(filter(lambda p: p['type'] == 'web', c['platforms'])
                           ), clients_with_self_hosted_apps))

    return [elm for clnt in mapped_list for elm in clnt]
