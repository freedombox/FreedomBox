# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app for System Monitoring (cockpit-pcp) in ‘System’.
"""

import subprocess
from functools import lru_cache

from django.utils.functional import lazy
from django.utils.translation import ugettext_lazy as _

from plinth.utils import Version


@lru_cache
def _get_url():
    """Return the web client URL based on Cockpit version."""
    process = subprocess.run(
        ['dpkg-query', '--showformat=${Version}', '--show', 'cockpit'],
        stdout=subprocess.PIPE)
    cockpit_version = process.stdout.decode()
    if Version(cockpit_version) >= Version('235'):
        url = '/_cockpit/metrics'
    else:
        url = '/_cockpit/system/graphs'

    return url


get_url = lazy(_get_url, str)

clients = [{
    'name': _('Cockpit'),
    'platforms': [{
        'type': 'web',
        'url': get_url()
    }]
}]
