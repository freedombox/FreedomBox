# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the JSXC module
"""

from django.conf.urls import url
from stronghold.decorators import public

from plinth.views import AppView

from .views import JsxcView

urlpatterns = [
    url(r'^apps/jsxc/$', AppView.as_view(app_id='jsxc'), name='index'),
    url(r'^apps/jsxc/jsxc/$', public(JsxcView.as_view()), name='jsxc')
]
