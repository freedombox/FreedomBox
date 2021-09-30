# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the samba module.
"""

from django.urls import re_path

from . import views

urlpatterns = [
    re_path(r'^apps/samba/$', views.SambaAppView.as_view(), name='index'),
    re_path(r'^apps/samba/share/(?P<mount_point>[A-Za-z0-9%_.\-~]+)/$',
            views.share, name='share')
]
