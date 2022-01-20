# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the Single Sign On module.
"""

from axes.decorators import axes_dispatch
from django.urls import re_path
from stronghold.decorators import public

from plinth.utils import non_admin_view

from .views import CaptchaLoginView, SSOLoginView, refresh

urlpatterns = [
    re_path(r'^accounts/sso/login/$',
            public(axes_dispatch(SSOLoginView.as_view())), name='sso-login'),
    re_path(r'^accounts/sso/refresh/$', non_admin_view(refresh),
            name='sso-refresh'),

    # Locked URL from django-axes
    re_path(r'accounts/sso/login/locked/$', public(CaptchaLoginView.as_view()),
            name='locked_out'),
]
