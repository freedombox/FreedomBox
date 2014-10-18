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

from django.conf.urls import patterns, url
from .views import State0View


urlpatterns = patterns(  # pylint: disable-msg=C0103
    'plinth.modules.first_boot.views',
    # Take care of the firstboot middleware when changing URLs
    url(r'^firstboot/$', State0View.as_view(), name='index'),
    url(r'^firstboot/state0/$', State0View.as_view(), name='state0'),
    url(r'^firstboot/state10/$', 'state10', name='state10'),
    )
