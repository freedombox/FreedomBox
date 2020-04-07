# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Django URLconf file containing all urls
"""
from captcha import views as cviews
from django.conf.urls import url
from stronghold.decorators import public

from plinth.modules.sso.views import CaptchaLoginView

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^language-selection/$',
        public(views.LanguageSelectionView.as_view()),
        name='language-selection'),
    url(r'^apps/$', views.AppsIndexView.as_view(), name='apps'),
    url(r'^sys/$', views.system_index, name='system'),

    # captcha urls are public
    url(r'^captcha/image/(?P<key>\w+)/$', public(cviews.captcha_image),
        name='captcha-image', kwargs={'scale': 1}),
    url(r'^captcha/image/(?P<key>\w+)@2/$', public(cviews.captcha_image),
        name='captcha-image-2x', kwargs={'scale': 2}),
    url(r'^captcha/audio/(?P<key>\w+)/$', public(cviews.captcha_audio),
        name='captcha-audio'),
    url(r'^captcha/refresh/$', public(cviews.captcha_refresh),
        name='captcha-refresh'),

    # locked url from django-axes
    url(r'locked/$', public(CaptchaLoginView.as_view()), name='locked_out'),

    # Notifications
    url(r'^notification/(?P<id>[A-Za-z0-9-=]+)/dismiss/$',
        views.notification_dismiss, name='notification_dismiss')
]
