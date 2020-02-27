# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the service discovery module.
"""

from django.conf.urls import url

from plinth.modules.avahi import AvahiAppView

urlpatterns = [
    url(r'^sys/avahi/$', AvahiAppView.as_view(), name='index'),
]
