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
Plinth module to configure reStore.
"""

from django.utils.translation import ugettext_lazy as _
from plinth import action_utils, cfg
from plinth import service as service_module

service = None

__all__ = ['init']

depends = ['plinth.modules.apps']


def init():
    """Initialize the reStore module."""
    menu = cfg.main_menu.get('apps:index')
    menu.add_urlname(_('Unhosted Storage (reStore)'), 'glyphicon-hdd',
                     'restore:index', 750)

    global service
    service = service_module.Service(
        'node-restore', _('reStore'), ['http', 'https'],
        is_external=False, enabled=is_enabled())


def is_enabled():
    """Return whether the module is enabled."""
    return action_utils.service_is_enabled('node-restore')
