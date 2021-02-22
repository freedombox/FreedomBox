# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the Zoph module.
"""

from django.conf.urls import url

from .views import SetupView, ZophAppView

urlpatterns = [
    url(r'^apps/zoph/setup/$', SetupView.as_view(), name='setup'),
    url(r'^apps/zoph/$', ZophAppView.as_view(app_id='zoph'), name='index')
]
