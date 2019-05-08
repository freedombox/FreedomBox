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
Django URL patterns for running tests.
"""

from django.conf.urls import url
from django.views.generic import TemplateView

_test_view = TemplateView.as_view(template_name='index.html')
urlpatterns = [
    url(r'^$', _test_view, name='index'),
    url(r'^apps/$', _test_view, name='apps'),
    url(r'^sys/$', _test_view, name='system'),
    url(r'^test/(?P<a>\d+)/(?P<b>\d+)/(?P<c>\d+)/$', _test_view, name='test'),
]
