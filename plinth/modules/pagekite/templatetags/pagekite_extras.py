# SPDX-License-Identifier: AGPL-3.0-or-later

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
