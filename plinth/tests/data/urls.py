# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Django URL patterns for running tests.
"""

from django.conf.urls import url
from django.views.generic import TemplateView

_test_view = TemplateView.as_view(template_name='index.html')
urlpatterns = [
    url(r'^$', _test_view, name='index'),
    url(r'^apps/$', _test_view, name='apps'),
    url(r'^sys/$', _test_view, name='system'),
    url(r'^test/(?P<a>\d+)/(?P<b>\d+)/(?P<c>\d+)/$', _test_view, name='test'),
]
