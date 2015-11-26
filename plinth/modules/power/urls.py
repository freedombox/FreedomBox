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
URLs for the power module.
"""

from django.conf.urls import patterns, url

urlpatterns = patterns(
    'plinth.modules.power.views',
    url(r'^sys/power/$', 'index', name='index'),
    url(r'^sys/power/reboot$', 'reboot', name='reboot'),
    url(r'^sys/power/reboot/now$', 'reboot_now', name='reboot_now'),
    url(r'^sys/power/shutdown$', 'shutdown', name='shutdown'),
    url(r'^sys/power/shutdown/now$', 'shutdown_now', name='shutdown_now'),
    )
