# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the bepasty module.
"""

from django.conf.urls import url

from .views import AddPasswordView, BepastyView, remove

urlpatterns = [
    url(r'^apps/bepasty/$', BepastyView.as_view(), name='index'),
    url(r'^apps/bepasty/add/$', AddPasswordView.as_view(), name='add'),
    url(r'^apps/bepasty/(?P<password>[A-Za-z0-9]+)/remove/$', remove,
        name='remove'),
]
