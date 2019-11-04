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
URLs for the Single Sign On module.
"""

from django.conf.urls import url

from .views import SSOLoginView, refresh
from stronghold.decorators import public
from plinth.utils import non_admin_view

urlpatterns = [
    url(r'^accounts/sso/login/$', public(SSOLoginView.as_view()),
        name='sso-login'),
    url(r'^accounts/sso/refresh/$', non_admin_view(refresh),
        name='sso-refresh'),
]
