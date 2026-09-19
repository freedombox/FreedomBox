# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the date and time module
"""

from django.urls import re_path

from .views import DateTimeAppView

urlpatterns = [
    re_path(r'^sys/datetime/$', DateTimeAppView.as_view(), name='index'),
]
