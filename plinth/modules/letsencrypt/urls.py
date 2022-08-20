# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the Let's Encrypt module.
"""

from django.urls import re_path

from . import views

urlpatterns = [
    re_path(r'^sys/letsencrypt/$', views.LetsEncryptAppView.as_view(),
            name='index'),
    re_path(r'^sys/letsencrypt/obtain/(?P<domain>[^/]+)/$', views.obtain,
            name='obtain'),
    re_path(r'^sys/letsencrypt/re-obtain/(?P<domain>[^/]+)/$', views.reobtain,
            name='re-obtain'),
    re_path(r'^sys/letsencrypt/revoke/(?P<domain>[^/]+)/$', views.revoke,
            name='revoke'),
    re_path(r'^sys/letsencrypt/delete/(?P<domain>[^/]+)/$', views.delete,
            name='delete'),
]
