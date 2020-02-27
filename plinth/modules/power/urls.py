# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the power module.
"""

from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^sys/power/$', views.index, name='index'),
    url(r'^sys/power/restart$', views.restart, name='restart'),
    url(r'^sys/power/shutdown$', views.shutdown, name='shutdown'),
]
