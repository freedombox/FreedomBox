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
URLs for the Syncthing module.
"""

from django.conf.urls import url

from plinth.modules import syncthing
from plinth.views import AppView

urlpatterns = [
    url(
        r'^apps/syncthing/$',
        AppView.as_view(app_id='syncthing', name=syncthing.name,
                        diagnostics_module_name='syncthing',
                        description=syncthing.description,
                        clients=syncthing.clients,
                        manual_page=syncthing.manual_page,
                        show_status_block=True), name='index'),
]
