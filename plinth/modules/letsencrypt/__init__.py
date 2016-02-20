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

from plinth import action_utils
from plinth import cfg
from plinth.modules import names
from plinth.utils import format_lazy


version = 1

is_essential = True

depends = ['apps', 'names']

title = _('Certificates (Let\'s Encrypt)')

description = [
    format_lazy(
        _('A digital certficate allows users of a web service to verify the '
          'identity of the service and to securely communicate with it. '
          '{box_name} can automatically obtain and setup digital '
          'certificates for each available domain.  It does so by proving '
          'itself to be the owner of a domain to Let\'s Encrypt, a '
          'certficate authority (CA).'), box_name=_(cfg.box_name)),

    _('Let\'s Encrypt is a free, automated, and open certificate '
      'authority, run for the public’s benefit by the Internet Security '
      'Research Group (ISRG).  Please read and agree with the '
      '<a href="https://letsencrypt.org/repository/">Let\'s Encrypt '
      'Subscriber Agreement</a> before using this service.')
]


service = None


def init():
    """Intialize the module."""
    menu = cfg.main_menu.get('system:index')
    menu.add_urlname(_('Certificates (Let\'s Encrypt)'),
                     'glyphicon-lock', 'letsencrypt:index', 20)


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(['letsencrypt'])


def diagnose():
    """Run diagnostics and return the results."""
    results = []

    for domain_type, domains in names.domains.items():
        if domain_type == 'hiddenservice':
            continue

        for domain in domains:
            results.append(action_utils.diagnose_url('https://' + domain))

    return results
