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

Currently that's functionality for converting pagekite service_on strings like
    "http:@kitename:localhost:80:@kitestring"
into parameter dictionaries and the other way round.
"""

SERVICE_PARAMS = ['protocol', 'kitename', 'backend_host', 'backend_port',
                  'secret']


def construct_params(string):
    """ Convert a parameter string into a params dictionary"""
    try:
        params = dict(zip(SERVICE_PARAMS, string.split(':')))
    except:
        msg = """params are expected to be a ':'-separated string
                            containing values for: %s , for example:\n"--params
                            http:@kitename:localhost:8000:@kitesecret"
                            """
        raise ValueError(msg % ", ".join(SERVICE_PARAMS))
    return params


def deconstruct_params(params):
    """ Convert params into a ":"-separated parameter string """
    try:
        paramstring = ":".join([params[param] for param in SERVICE_PARAMS])
    except KeyError:
        raise ValueError("Could not parse params: %s " % params)
    return paramstring
