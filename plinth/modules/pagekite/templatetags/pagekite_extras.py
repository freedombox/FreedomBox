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

from django import template
from plinth.modules.pagekite import utils

register = template.Library()


@register.simple_tag
def create_pagekite_service_url(service, kite_name):
    """Create a URL out of a pagekite service

    Parameters: - service: the service params dictionary
                - kite_name: kite name from the pagekite configuration, not
                             from the service params
    """
    # add extra information if it's missing
    if 'subdomains' not in service:
        service = utils.prepare_service_for_display(service)

    urlparams = {'protocol': service['protocol']}
    if service['subdomains']:
        urlparams['kite_name'] = "*.%s" % kite_name
    else:
        urlparams['kite_name'] = kite_name
    url = "{protocol}://{kite_name}".format(**urlparams)
    if 'frontend_port' in service and service['frontend_port']:
        url = "%s:%s" % (url, service['frontend_port'])
    return url
