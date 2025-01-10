# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Django URLconf file containing all urls
"""
from captcha import views as cviews
from django.urls import include, re_path
from stronghold.decorators import public

from . import views

system_urlpatterns = [
    re_path(r'^sys/$', views.system_index, name='visibility'),
    re_path(r'^sys/$', views.system_index, name='data'),
    re_path(r'^sys/$', views.system_index, name='system'),
    re_path(r'^sys/$', views.system_index, name='security'),
    re_path(r'^sys/$', views.system_index, name='administration'),
]

urlpatterns = [
    re_path(r'^$', views.index, name='index'),
    re_path(r'^language-selection/$',
            public(views.LanguageSelectionView.as_view()),
            name='language-selection'),
    re_path(r'^apps/$', views.AppsIndexView.as_view(), name='apps'),
    re_path(r'^sys/$', views.system_index, name='system'),
    re_path(r'', include((system_urlpatterns, 'system'))),
    re_path(r'^uninstall/(?P<app_id>[1-9a-z\-_]+)/$',
            views.UninstallView.as_view(), name='uninstall'),
    re_path(r'^rerun-setup/(?P<app_id>[1-9a-z\-_]+)/$', views.rerun_setup_view,
            name='rerun-setup'),

    # captcha urls are public
    re_path(r'^captcha/image/(?P<key>\w+)/$', public(cviews.captcha_image),
            name='captcha-image', kwargs={'scale': 1}),
    re_path(r'^captcha/image/(?P<key>\w+)@2/$', public(cviews.captcha_image),
            name='captcha-image-2x', kwargs={'scale': 2}),
    re_path(r'^captcha/audio/(?P<key>\w+)/$', public(cviews.captcha_audio),
            name='captcha-audio'),
    re_path(r'^captcha/refresh/$', public(cviews.captcha_refresh),
            name='captcha-refresh'),

    # Notifications
    re_path(r'^notification/(?P<id>[A-Za-z0-9-=]+)/dismiss/$',
            views.notification_dismiss, name='notification_dismiss')
]
