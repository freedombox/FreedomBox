# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the minidlna Server module.
"""

from django.urls import re_path

from plinth.modules.minidlna.views import MiniDLNAAppView

urlpatterns = [
    re_path(r'^apps/minidlna/$', MiniDLNAAppView.as_view(), name='index'),
]
