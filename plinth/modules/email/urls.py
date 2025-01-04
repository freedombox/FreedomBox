# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the email module.
"""

from django.urls import path, re_path
from stronghold.decorators import public

from plinth.utils import non_admin_view

from . import views

urlpatterns = [
    path('apps/email/', views.EmailAppView.as_view(), name='index'),
    re_path('apps/email/dns/(?P<domain>[^/]+)/$', views.DnsView.as_view(),
            name='dns'),
    path('apps/email/aliases/', non_admin_view(views.AliasView.as_view()),
         name='aliases'),
    path('apps/email/config.xml', public(views.XmlView.as_view())),
]
