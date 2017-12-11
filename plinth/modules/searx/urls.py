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
URLs for the Searx module.
"""

from django.conf.urls import url

from plinth.modules import searx
from plinth.views import ServiceView

urlpatterns = [
    url(r'^apps/searx/$',
        ServiceView.as_view(
            service_id='searx', diagnostics_module_name='searx',
            description=searx.description, clients=searx.clients,
            show_status_block=False), name='index'),
]
