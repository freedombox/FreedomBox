# SPDX-License-Identifier: AGPL-3.0-or-later
"""URLs for the Apache module."""

from django.urls import re_path
from stronghold.decorators import public

from .views import DiscoverIDPView

urlpatterns = [
    re_path(r'^apache/discover-idp/$', public(DiscoverIDPView.as_view()),
            name='discover-idp'),
]
