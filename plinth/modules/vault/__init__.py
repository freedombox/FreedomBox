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
Vault - a simple admin interface for the freedombox
"""

from plinth import cfg
from .registry import register_app, register_service, register_statusline

def init():
    cfg.main_menu.add_urlname("Simple Mode", "glyphicon-th-large", 
                              "vault:apps", 110)

__all__ = [init, register_app, register_service, register_statusline]

DEPENDS = []
