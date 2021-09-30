# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the Tahoe-LAFS module.
"""

from django.urls import re_path

from . import views
from .views import TahoeAppView, TahoeSetupView

urlpatterns = [
    re_path(r'^apps/tahoe/setup/$', TahoeSetupView.as_view(), name='setup'),
    re_path(r'^apps/tahoe/add_introducer/$', views.add_introducer,
            name='add-introducer'),
    re_path(r'^apps/tahoe/remove_introducer/(?P<introducer>[0-9a-zA-Z_]+)/$',
            views.remove_introducer, name='remove-introducer'),
    re_path(r'^apps/tahoe/$', TahoeAppView.as_view(), name='index')
]
