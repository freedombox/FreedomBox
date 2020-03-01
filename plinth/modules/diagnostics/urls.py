# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the Diagnostics module
"""

from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^sys/diagnostics/$', views.index, name='index'),
    url(r'^sys/diagnostics/(?P<app_id>[1-9a-z\-]+)/$', views.diagnose_app,
        name='app'),
]
