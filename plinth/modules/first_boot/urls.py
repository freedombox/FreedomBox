# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the First Boot module
"""

from django.conf.urls import url
from stronghold.decorators import public

from .views import CompleteView, WelcomeView

urlpatterns = [
    # Take care of the firstboot middleware when changing URLs
    url(r'^firstboot/$', public(WelcomeView.as_view()), name='index'),
    url(r'^firstboot/welcome/$', public(WelcomeView.as_view()),
        name='welcome'),
    url(r'^firstboot/complete/$', CompleteView.as_view(), name='complete'),
]
