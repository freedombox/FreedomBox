# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the dynamicdns module
"""

from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^sys/dynamicdns/$', views.index, name='index'),
    url(r'^sys/dynamicdns/configure/$', views.configure, name='configure'),
    url(r'^sys/dynamicdns/statuspage/$', views.statuspage, name='statuspage'),
]
