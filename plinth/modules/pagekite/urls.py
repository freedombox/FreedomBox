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
URLs for the PageKite module
"""

from django.conf.urls import url

from .views import StandardServiceView, CustomServiceView, ConfigurationView, \
    DeleteServiceView, index


urlpatterns = [
    url(r'^sys/pagekite/$', index, name='index'),
    url(r'^sys/pagekite/configure/$', ConfigurationView.as_view(),
        name='configure'),
    url(r'^sys/pagekite/services/standard$', StandardServiceView.as_view(),
        name='standard-services'),
    url(r'^sys/pagekite/services/custom$', CustomServiceView.as_view(),
        name='custom-services'),
    url(r'^sys/pagekite/services/custom/delete$', DeleteServiceView.as_view(),
        name='delete-custom-service'),
]
