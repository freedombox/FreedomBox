# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the name services module
"""

from django.urls import re_path

from . import views

urlpatterns = [
    re_path(r'^sys/names/$', views.index, name='index'),
]
