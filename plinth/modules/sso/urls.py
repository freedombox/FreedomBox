# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the Single Sign On module.
"""

from django.conf.urls import url

from .views import SSOLoginView, refresh
from stronghold.decorators import public
from plinth.utils import non_admin_view

urlpatterns = [
    url(r'^accounts/sso/login/$', public(SSOLoginView.as_view()),
        name='sso-login'),
    url(r'^accounts/sso/refresh/$', non_admin_view(refresh),
        name='sso-refresh'),
]
