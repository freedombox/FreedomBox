# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the Firewall module
"""

from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^sys/firewall/$', views.FirewallAppView.as_view(), name='index'),
]
