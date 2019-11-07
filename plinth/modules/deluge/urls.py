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
URLs for the Deluge module.
"""

from django.conf.urls import url

from plinth.modules import deluge
from plinth.views import AppView

urlpatterns = [
    url(
        r'^apps/deluge/$',
        AppView.as_view(name=deluge.name, description=deluge.description,
                        diagnostics_module_name='deluge',
                        clients=deluge.clients, app_id='deluge',
                        manual_page=deluge.manual_page, icon_filename=deluge.icon_filename), name='index'),
]
