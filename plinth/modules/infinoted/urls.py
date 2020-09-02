# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the infinoted module.
"""

from django.conf.urls import url

from plinth.views import AppView

urlpatterns = [
    url(r'^apps/infinoted/$', AppView.as_view(app_id='infinoted'),
        name='index'),
]
