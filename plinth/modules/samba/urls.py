# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the samba module.
"""

from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^apps/samba/$', views.SambaAppView.as_view(), name='index'),
    url(r'^apps/samba/share/(?P<mount_point>[A-Za-z0-9%_.\-~]+)/$',
        views.share, name='share')
]
