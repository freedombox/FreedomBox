# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the name services module
"""

from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^sys/names/$', views.index, name='index'),
]
