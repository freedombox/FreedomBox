# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the dynamicdns module
"""

from django.urls import re_path

from . import views

urlpatterns = [
    re_path(r'^sys/dynamicdns/$', views.index, name='index'),
    re_path(r'^sys/dynamicdns/statuspage/$', views.statuspage,
            name='statuspage'),
]
