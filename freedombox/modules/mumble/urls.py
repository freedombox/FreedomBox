# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the Mumble module
"""

from django.urls import re_path

from plinth.modules.mumble.views import MumbleAppView

urlpatterns = [
    re_path(r'^apps/mumble/$', MumbleAppView.as_view(), name='index'),
]
