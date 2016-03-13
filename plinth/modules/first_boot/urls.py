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

from .views import State0View, State1View, State5View, state10


urlpatterns = [
    # Take care of the firstboot middleware when changing URLs
    url(r'^firstboot/$', public(State0View.as_view()), name='index'),
    url(r'^firstboot/state0/$', public(State0View.as_view()), name='state0'),
    url(r'^firstboot/state1/$', public(State1View.as_view()), name='state1'),
    url(r'^firstboot/state5/$', State5View.as_view(), name='state5'),
    url(r'^firstboot/state10/$', state10, name='state10'),
]
