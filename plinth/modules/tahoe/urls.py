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
URLs for the Tahoe-LAFS module.
"""

from . import views

from django.conf.urls import url

from .views import TahoeSetupView, TahoeServiceView


urlpatterns = [
    url(r'^apps/tahoe-lafs/setup$', TahoeSetupView.as_view(),
        name='setup'),
    url(r'^apps/tahoe-lafs/add_introducer$', views.add_introducer,
        name="add-introducer"),
    url(r'^apps/tahoe-lafs/remove_introducer/(?P<introducer>[0-9a-zA-Z_]+)$',
        views.remove_introducer, name="remove-introducer"),
    url(r'^apps/tahoe-lafs/$', TahoeServiceView.as_view(),
        name='index')
]
