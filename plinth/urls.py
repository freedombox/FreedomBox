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
Django URLconf file containing all urls
"""
from captcha import views as cviews
from django.conf.urls import url
from django.views.generic import TemplateView

from plinth.modules.sso.views import CaptchaLoginView
from stronghold.decorators import public

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^apps/$',
        TemplateView.as_view(template_name='apps.html'),
        name='apps'),
    url(r'^sys/$', views.system_index, name='system'),

    # captcha urls are public
    url(r'image/(?P<key>\w+)/$',
        public(cviews.captcha_image),
        name='captcha-image',
        kwargs={'scale': 1}),
    url(r'image/(?P<key>\w+)@2/$',
        public(cviews.captcha_image),
        name='captcha-image-2x',
        kwargs={'scale': 2}),
    url(r'audio/(?P<key>\w+)/$', public(cviews.captcha_audio), name='captcha-audio'),
    url(r'refresh/$', public(cviews.captcha_refresh), name='captcha-refresh'),
    url(r'locked/$', public(CaptchaLoginView.as_view()), name='locked_out'),
]
