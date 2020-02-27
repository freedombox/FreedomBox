# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the plinth api for android app.
"""

from django.conf.urls import url
from stronghold.decorators import public

from plinth.modules.api import views

urlpatterns = [
    url(r'^api/(?P<version>[0-9]+)/shortcuts/?$', public(views.shortcuts)),
    url(r'^api/(?P<version>[0-9]+)/access-info/?$', public(views.access_info)),
]
