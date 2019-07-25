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
Overridden AppConfig from django-axes to avoid monkey-patched LoginView
"""

from django import apps


class AppConfig(apps.AppConfig):
    name = 'axes'

    def ready(self):
        # Signals must be loaded for axes to get the login_failed signals
        from axes import signals  # noqa pylint: disable=unused-import isort:skip
