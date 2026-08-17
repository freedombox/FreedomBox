# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the minetest module.
"""

from django.urls import re_path

from plinth.modules.minetest.views import MinetestAppView

urlpatterns = [
    re_path(r'^apps/minetest/$', MinetestAppView.as_view(), name='index-old'),
    re_path(r'^apps/luanti/$', MinetestAppView.as_view(), name='index'),
]
