# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Test modules for Pagekite functions.
"""

from plinth.modules.pagekite import utils

_tests = [
    {
        'line': 'https/8080:*.@kitename:localhost:8080:@kitesecret',
        'params': {
            'kitename': '*.@kitename',
            'backend_host': 'localhost',
            'secret': '@kitesecret',
            'protocol': 'https/8080',
            'backend_port': '8080'
        }
    },
    {
        'line': 'https:*.@kitename:localhost:80:@kitesecret',
        'params': {
            'protocol': 'https',
            'kitename': '*.@kitename',
            'backend_port': '80',
            'backend_host': 'localhost',
            'secret': '@kitesecret'
        }
    },
    {
        'line': 'raw/22:@kitename:localhost:22:@kitesecret',
        'params': {
            'protocol': 'raw/22',
            'kitename': '@kitename',
            'backend_port': '22',
            'backend_host': 'localhost',
            'secret': '@kitesecret'
        }
    },
]


def test_convert_service_to_string():
    """ Test deconstructing parameter dictionaries into strings """
    for test in _tests:
        service_string = utils.convert_service_to_string(test['params'])
        assert test['line'] == service_string
