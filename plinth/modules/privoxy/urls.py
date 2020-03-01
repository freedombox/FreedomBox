# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the Privoxy module.
"""

from django.conf.urls import url

from plinth.views import AppView

urlpatterns = [
    url(r'^apps/privoxy/$', AppView.as_view(app_id='privoxy'), name='index'),
]
