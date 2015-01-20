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

import copy
import os
from django import template

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

        match = os.path.commonprefix([urlitem['url'], path])
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


@register.assignment_tag
def create_pagekite_service_link(service, kite_name):
    """Create a link (URL) out of a pagekite service

    Parameters: - service: the params dictionary
                - kite_name: kite name (from the pagekite configuration)
    """
    params = {'protocol': service['protocol']}
    if 'subdomains' in service and service['subdomains']:
        params['kite_name'] = "*.%s" % kite_name
    else:
        params['kite_name'] = kite_name
    link = "{protocol}://{kite_name}".format(**params)
    if 'frontend_port' in service and service['frontend_port']:
        link = "%s:%s" % (link, service['frontend_port'])
    return link
