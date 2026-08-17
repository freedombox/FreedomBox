# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the Kiwix module.
"""

from django.urls import re_path

from . import views

urlpatterns = [
    re_path(r'^apps/kiwix/$', views.KiwixAppView.as_view(), name='index'),
    re_path(r'^apps/kiwix/package/add/$', views.AddPackageView.as_view(),
            name='add-package'),
    re_path(r'^apps/kiwix/package/(?P<zim_id>[a-zA-Z0-9-]+)/delete/$',
            views.delete_package, name='delete-package'),
]
