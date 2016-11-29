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
URLs for the ikiwiki module
"""

from django.conf.urls import url

from . import views
from plinth.views import UninstallView


urlpatterns = [
    url(r'^apps/ikiwiki/$',
        views.IkiwikiServiceView.as_view(), name='index'),
    url(r'^apps/ikiwiki/manage/$', views.manage, name='manage'),
    url(r'^apps/ikiwiki/(?P<name>[\w.@+-]+)/delete/$', views.delete,
        name='delete'),
    url(r'^apps/ikiwiki/create/$', views.create, name='create'),
    url(r'^apps/ikiwiki/uninstall/$',
        UninstallView.as_view(), name='uninstall'),
]
