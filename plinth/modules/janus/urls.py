# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the janus app.
"""

from django.urls import re_path
from stronghold.decorators import public

from plinth.views import AppView

from .views import JanusRoomView

urlpatterns = [
    re_path(r'^apps/janus/$', AppView.as_view(app_id='janus'), name='index'),
    re_path(r'^apps/janus/room/$', public(JanusRoomView.as_view()),
            name='room')
]
