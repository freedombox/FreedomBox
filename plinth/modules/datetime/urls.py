# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the date and time module
"""

from django.conf.urls import url

from .views import DateTimeAppView

urlpatterns = [
    url(r'^sys/datetime/$', DateTimeAppView.as_view(), name='index'),
]
