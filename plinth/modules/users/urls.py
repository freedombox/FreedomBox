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
URLs for the Users module
"""

from django.conf.urls import patterns, url
from django.views.generic import RedirectView


urlpatterns = patterns(  # pylint: disable-msg=C0103
    'plinth.modules.users.users',
    # create an index page (that only forwards) to have correct highlighting
    # of submenu items
    url(r'^sys/users/$', RedirectView.as_view(pattern_name='users:add'),
        name='index'),
    url(r'^sys/users/add/$', 'add', name='add'),
    url(r'^sys/users/edit/$', 'edit', name='edit'),
)
