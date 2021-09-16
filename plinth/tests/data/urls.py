# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Django URL patterns for running tests.
"""

from django.urls import re_path
from django.views.generic import TemplateView

_test_view = TemplateView.as_view(template_name='index.html')
urlpatterns = [
    re_path(r'^$', _test_view, name='index'),
    re_path(r'^apps/$', _test_view, name='apps'),
    re_path(r'^sys/$', _test_view, name='system'),
    re_path(r'^test/(?P<a>\d+)/(?P<b>\d+)/(?P<c>\d+)/$', _test_view,
            name='test'),
]
