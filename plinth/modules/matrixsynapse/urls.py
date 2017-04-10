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
URLs for the matrix-synapse module.
"""

from django.conf.urls import url

from .views import SetupView, ServiceView

urlpatterns = [
    url(r'^apps/matrixsynapse/setup/$', SetupView.as_view(), name='setup'),
    url(r'^apps/matrixsynapse/$', ServiceView.as_view(), name='index'),
]
