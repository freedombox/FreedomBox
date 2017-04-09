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
URLs for the monkeysphere module.
"""

from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^sys/monkeysphere/$', views.index, name='index'),
    url(r'^sys/monkeysphere/(?P<ssh_fingerprint>[0-9A-Za-z:+/]+)/import/$',
        views.import_key, name='import'),
    url(r'^sys/monkeysphere/(?P<fingerprint>[0-9A-Fa-f]+)/details/$',
        views.details, name='details'),
    url(r'^sys/monkeysphere/(?P<fingerprint>[0-9A-Fa-f]+)/publish/$',
        views.publish, name='publish'),
    url(r'^sys/monkeysphere/cancel/$', views.cancel, name='cancel'),
]
