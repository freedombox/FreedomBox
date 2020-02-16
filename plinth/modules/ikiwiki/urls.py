# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the ikiwiki module
"""

from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^apps/ikiwiki/$', views.IkiwikiAppView.as_view(), name='index'),
    url(r'^apps/ikiwiki/(?P<name>.+)/delete/$', views.delete, name='delete'),
    url(r'^apps/ikiwiki/create/$', views.create, name='create'),
]
