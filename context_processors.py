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

import re
import cfg


def plinth_processor(request):
    """Add additional context values to RequestContext for use in templates"""
    slash_indizes = [m.start() for m in re.finditer('/', request.path)]
    active_menu_urls = [request.path[:index+1] for index in slash_indizes]
    return {
        'cfg': cfg,
        'submenu': cfg.main_menu.active_item(request),
        'active_menu_urls': active_menu_urls
    }
