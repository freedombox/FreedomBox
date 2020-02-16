# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the Mumble module
"""

from django.conf.urls import url

from plinth.modules.mumble.views import MumbleAppView

urlpatterns = [
    url(r'^apps/mumble/$', MumbleAppView.as_view(), name='index'),
]
