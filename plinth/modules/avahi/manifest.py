#
# This file is part of FreedomBox.
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
Application manifest for avahi.
"""

from plinth.modules.backups.api import validate as validate_backup

# Services that intend to make themselves discoverable will drop files into
# /etc/avahi/services. Currently, we don't intend to make that customizable.
# There is no necessity for backup and restore. This manifest will ensure that
# avahi enable/disable setting is preserved.
backup = validate_backup({})
