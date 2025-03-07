# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the dynamicdns module
"""

from django.urls import re_path

from . import views

urlpatterns = [
    re_path(r'^sys/dynamicdns/$', views.DynamicDNSAppView.as_view(),
            name='index'),
    re_path(r'^sys/dynamicdns/domain/add/$', views.DomainView.as_view(),
            name='domain-add'),
    re_path(r'^sys/dynamicdns/domain/(?P<domain>[^/]+)/edit/$',
            views.DomainView.as_view(), name='domain-edit'),
    re_path(r'^sys/dynamicdns/domain/(?P<domain>[^/]+)/delete/$',
            views.DomainDeleteView.as_view(), name='domain-delete'),
]
