# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the bepasty module.
"""

from django.urls import re_path

from .views import AddPasswordView, BepastyView, remove

urlpatterns = [
    re_path(r'^apps/bepasty/$', BepastyView.as_view(), name='index'),
    re_path(r'^apps/bepasty/add/$', AddPasswordView.as_view(), name='add'),
    re_path(r'^apps/bepasty/(?P<password>[A-Za-z0-9]+)/remove/$', remove,
            name='remove'),
]
