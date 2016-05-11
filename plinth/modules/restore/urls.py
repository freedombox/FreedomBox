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
URLs for the reStore module.
"""

from django.conf.urls import url

from plinth.views import ServiceView
from plinth.modules import restore


urlpatterns = [
    url(r'^apps/restore/$', ServiceView.as_view(
            service_id=restore.managed_services[0],
            description=restore.description
        ), name='index'),
]
