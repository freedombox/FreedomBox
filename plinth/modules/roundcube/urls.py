# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the Roundcube module.
"""

from django.conf.urls import url

from plinth.views import AppView

urlpatterns = [
    url(r'^apps/roundcube/$', AppView.as_view(app_id='roundcube'),
        name='index')
]
