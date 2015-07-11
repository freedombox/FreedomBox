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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

"""
URLs for the upgrades module
"""

from django.conf.urls import patterns, url


urlpatterns = patterns(
    'plinth.modules.upgrades.upgrades',
    url(r'^sys/upgrades/$', 'index', name='index'),
    url(r'^sys/upgrades/run/$', 'run', name='run'),
    url(r'^sys/upgrades/configure/$', 'configure', name='configure'),
    )
