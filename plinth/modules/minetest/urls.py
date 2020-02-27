# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the minetest module.
"""

from django.conf.urls import url

from plinth.modules.minetest.views import MinetestAppView

urlpatterns = [
    url(r'^apps/minetest/$', MinetestAppView.as_view(), name='index'),
]
