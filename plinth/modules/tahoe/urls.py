# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the Tahoe-LAFS module.
"""

from django.conf.urls import url

from . import views
from .views import TahoeAppView, TahoeSetupView

urlpatterns = [
    url(r'^apps/tahoe/setup/$', TahoeSetupView.as_view(), name='setup'),
    url(r'^apps/tahoe/add_introducer/$', views.add_introducer,
        name='add-introducer'),
    url(r'^apps/tahoe/remove_introducer/(?P<introducer>[0-9a-zA-Z_]+)/$',
        views.remove_introducer, name='remove-introducer'),
    url(r'^apps/tahoe/$', TahoeAppView.as_view(), name='index')
]
