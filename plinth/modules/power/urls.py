# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the power module.
"""

from django.urls import re_path

from . import views

urlpatterns = [
    re_path(r'^sys/power/$', views.index, name='index'),
    re_path(r'^sys/power/restart$', views.restart, name='restart'),
    re_path(r'^sys/power/shutdown$', views.shutdown, name='shutdown'),
]
