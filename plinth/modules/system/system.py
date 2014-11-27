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

from gettext import gettext as _
from django.template.response import TemplateResponse

from plinth import cfg


def init():
    """Initialize the system module"""
    cfg.main_menu.add_urlname(_('System'), 'glyphicon-cog', 'system:index', 100)


def index(request):
    """Serve the index page"""
    return TemplateResponse(request, 'system.html',
                            {'title': _('System Configuration')})
