# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the Zoph module.
"""

from django.urls import re_path

from .views import SetupView, ZophAppView

urlpatterns = [
    re_path(r'^apps/zoph/setup/$', SetupView.as_view(), name='setup'),
    re_path(r'^apps/zoph/$', ZophAppView.as_view(app_id='zoph'), name='index')
]
