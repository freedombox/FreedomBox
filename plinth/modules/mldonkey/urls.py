# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the mldonkey module.
"""

from django.conf.urls import url

from plinth.views import AppView

urlpatterns = [
    url(r'^apps/mldonkey/$',
        AppView.as_view(
            app_id='mldonkey',
            show_status_block=True,
        ), name='index'),
]
