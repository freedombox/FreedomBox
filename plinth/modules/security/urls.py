# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the security module
"""

from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^sys/security/$', views.index, name='index'),
    url(r'^sys/security/report$', views.report, name='report'),
]
