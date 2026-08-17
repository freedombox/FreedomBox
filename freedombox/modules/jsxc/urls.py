# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the JSXC module
"""

from django.urls import re_path
from stronghold.decorators import public

from plinth.views import AppView

from .views import JsxcView

urlpatterns = [
    re_path(r'^apps/jsxc/$', AppView.as_view(app_id='jsxc'), name='index'),
    re_path(r'^apps/jsxc/jsxc/$', public(JsxcView.as_view()), name='jsxc')
]
