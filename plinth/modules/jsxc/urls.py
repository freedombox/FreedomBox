# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the JSXC module
"""

from django.conf.urls import url
from stronghold.decorators import public

from .views import JSXCAppView, JsxcView

urlpatterns = [
    url(r'^apps/jsxc/$', JSXCAppView.as_view(), name='index'),
    url(r'^apps/jsxc/jsxc/$', public(JsxcView.as_view()), name='jsxc')
]
