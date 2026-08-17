# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the First Boot module
"""

from django.urls import re_path
from stronghold.decorators import public

from .views import CompleteView, WelcomeView

urlpatterns = [
    # Take care of the firstboot middleware when changing URLs
    re_path(r'^firstboot/$', public(WelcomeView.as_view()), name='index'),
    re_path(r'^firstboot/welcome/$', public(WelcomeView.as_view()),
            name='welcome'),
    re_path(r'^firstboot/complete/$', CompleteView.as_view(), name='complete'),
]
