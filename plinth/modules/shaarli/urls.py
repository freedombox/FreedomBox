# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the Shaarli module.
"""

from django.conf.urls import url

from plinth.views import AppView

urlpatterns = [
    url(r'^apps/shaarli/$', AppView.as_view(app_id='shaarli'), name='index')
]
