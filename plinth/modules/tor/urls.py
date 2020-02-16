# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the Tor module.
"""

from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^apps/tor/$', views.index, name='index'),
]
