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
URLs for the Vault module
"""

from django.conf.urls import patterns, url
from .views import Apps, Services


urlpatterns = patterns(
    'plinth.modules.vault.views',
    url(r'^vault/apps$', Apps.as_view(), name='apps'),
    url(r'^vault/services$', Services.as_view(), name='services'),
    url(r'^vault/enable/(.+)/$', 'enable_service',
        name='enable_service'),
    url(r'^vault/disable/(.+)/$', 'disable_service',
        name='disable_service'),
    )
