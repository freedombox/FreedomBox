# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the Let's Encrypt module.
"""

from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^sys/letsencrypt/$', views.index, name='index'),
    url(r'^sys/letsencrypt/obtain/(?P<domain>[^/]+)/$', views.obtain,
        name='obtain'),
    url(r'^sys/letsencrypt/re-obtain/(?P<domain>[^/]+)/$', views.reobtain,
        name='re-obtain'),
    url(r'^sys/letsencrypt/revoke/(?P<domain>[^/]+)/$', views.revoke,
        name='revoke'),
    url(r'^sys/letsencrypt/delete/(?P<domain>[^/]+)/$', views.delete,
        name='delete'),
]
