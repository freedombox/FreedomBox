# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the plinth api for android app.
"""

from django.urls import re_path
from stronghold.decorators import public

from plinth.modules.api import views

urlpatterns = [
    re_path(r'^api/(?P<version>[0-9]+)/shortcuts/?$', public(views.shortcuts)),
    re_path(r'^api/(?P<version>[0-9]+)/access-info/?$',
            public(views.access_info)),
]
