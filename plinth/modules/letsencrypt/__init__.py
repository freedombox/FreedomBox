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
Plinth module for using Let's Encrypt.
"""

from django.utils.translation import ugettext_lazy as _
import json

from plinth import actions
from plinth import action_utils
from plinth import cfg
from plinth import service as service_module
from plinth.modules import names


depends = [
    'plinth.modules.apps',
    'plinth.modules.names'
]

service = None


def init():
    """Intialize the module."""
    menu = cfg.main_menu.get('system:index')
    menu.add_urlname(_('Certificates (Let\'s Encrypt)'),
                     'glyphicon-lock', 'letsencrypt:index', 20)


def diagnose():
    """Run diagnostics and return the results."""
    results = []

    for domain_type, domains in names.domains.items():
        if domain_type == 'hiddenservice':
            continue

        for domain in domains:
            results.append(action_utils.diagnose_url('https://' + domain))

    return results
