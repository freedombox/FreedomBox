# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the minidlna Server module.
"""

from django.conf.urls import url

from plinth.modules.minidlna.views import MiniDLNAAppView

urlpatterns = [
    url(r'^apps/minidlna/$', MiniDLNAAppView.as_view(), name='index'),
]
