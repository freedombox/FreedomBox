#!/usr/bin/python2
# -*- mode: python -*-
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

"""
The variables/functions defined here are used by both the action script
and the plinth pagekite module.

For example the functionality to convert pagekite service_on strings like
    "http:@kitename:localhost:80:@kitestring"
into parameter dictionaries and the other way round. And functions that we want
to be covered by tests.
"""
# ATTENTION: This file has to be both python2 and python3 compatible

import os
import shlex
CONF_PATH = '/files/etc/pagekite.d'

SERVICE_PARAMS = ['protocol', 'kitename', 'backend_host', 'backend_port',
                  'secret']


def convert_to_service(service_string):
    """ Convert a service string into a service parameter dictionary"""
    # The actions.py uses shlex.quote() to escape/quote malicious user input.
    # That affects '*.@kitename', so the params string gets quoted.
    # If the string is escaped and contains '*.@kitename', look whether shlex
    # would still quote/escape the string when we remove '*.@kitename'.

    # TODO: use shlex only once augeas-python supports python3
    if hasattr(shlex, 'quote'):
        quotefunction = shlex.quote
    else:
        import pipes
        quotefunction = pipes.quote

    if service_string.startswith("'") and service_string.endswith("'"):
        unquoted_string = service_string[1:-1]
        error_msg = "The parameters contain suspicious characters: %s "
        if '*.@kitename' in service_string:
            unquoted_test_string = unquoted_string.replace('*.@kitename', '')
            if unquoted_test_string == quotefunction(unquoted_test_string):
                # no other malicious characters found, use the unquoted string
                service_string = unquoted_string
            else:
                raise RuntimeError(error_msg % service_string)
        else:
            raise RuntimeError(error_msg % service_string)

    try:
        params = dict(zip(SERVICE_PARAMS, service_string.split(':')))
    except Exception:
        msg = """params are expected to be a ':'-separated string containing
              values for: %s , for example:\n"--params
              http/8000:@kitename:localhost:8000:@kitesecret"
              """
        raise ValueError(msg % ", ".join(SERVICE_PARAMS))
    return params


def convert_service_to_string(service):
    """ Convert service dict into a ":"-separated parameter string """
    try:
        service_string = ":".join([str(service[param]) for param in
                                  SERVICE_PARAMS])
    except KeyError:
        raise ValueError("Could not parse params: %s " % service)
    return service_string


def get_augeas_servicefile_path(protocol):
    """Get the augeas path where a service for a protocol should be stored"""
    if not protocol.startswith(("http", "https", "raw")):
        raise ValueError('Unsupported protocol: %s' % protocol)

    try:
        _protocol, port = protocol.split('/')
    except ValueError:
        if protocol == 'http':
            relpath = '80_http.rc'
        elif protocol == 'https':
            relpath = '443_https.rc'
        else:
            raise ValueError('Unsupported protocol: %s' % protocol)
    else:
        relpath = '%s_%s.rc' % (port, _protocol)

    return os.path.join(CONF_PATH, relpath, 'service_on')
