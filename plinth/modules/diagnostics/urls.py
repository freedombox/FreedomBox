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
URLs for the Diagnostics module
"""

from django.conf.urls import patterns, url


urlpatterns = patterns(  # pylint: disable-msg=C0103
    'plinth.modules.diagnostics.diagnostics',
    url(r'^sys/diagnostics/$', 'index', name='index'),
    url(r'^sys/diagnostics/test/$', 'test', name='test'),
    url(r'^sys/diagnostics/module/(?P<module_name>[a-z\-]+)/$', 'module',
        name='module'),
    )
