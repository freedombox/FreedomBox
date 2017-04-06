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
Django context processors to provide common data to templates.
"""

from django.utils.translation import ugettext as _, ugettext_noop
import re

from plinth import cfg
from plinth.menu import main_menu
from plinth.utils import is_user_admin


def common(request):
    """Add additional context values to RequestContext for use in templates.

    Any resources referenced in the return value are expected to have been
    initialized or configured externally beforehand.
    """
    # Allow a value in configuration file to be translated.  Allow
    # the brand name 'FreedomBox' itself to be translated.
    ugettext_noop('FreedomBox')

    slash_indices = [match.start() for match in re.finditer('/', request.path)]
    active_menu_urls = [request.path[:index + 1] for index in slash_indices]
    return {
        'cfg': cfg,
        'submenu': main_menu.active_item(request),
        'active_menu_urls': active_menu_urls,
        'box_name': _(cfg.box_name),
        'user_is_admin': is_user_admin(request, True)
    }
