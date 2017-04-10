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
URLs for the First Boot module
"""

from django.conf.urls import url
from stronghold.decorators import public

from .views import WelcomeView, CompleteView


urlpatterns = [
    # Take care of the firstboot middleware when changing URLs
    url(r'^firstboot/$', public(WelcomeView.as_view()), name='index'),
    url(r'^firstboot/welcome/$', public(WelcomeView.as_view()),
        name='welcome'),
    url(r'^firstboot/complete/$', CompleteView.as_view(), name='complete'),
]
