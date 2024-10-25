# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the Help module
"""

from django.urls import re_path
from stronghold.decorators import public

from plinth.utils import non_admin_view

from . import views

urlpatterns = [
    re_path(r'^help/$', non_admin_view(views.index), name='index'),
    re_path(r'^help/about/$', public(views.about), name='about'),
    re_path(r'^help/feedback/$', non_admin_view(views.feedback),
            name='feedback'),
    re_path(r'^help/support/$', non_admin_view(views.support), name='support'),
    re_path(r'^help/contribute/$', non_admin_view(views.contribute),
            name='contribute'),
    re_path(r'^help/manual/$', non_admin_view(views.manual), name='manual'),
    re_path(r'^help/manual/(?P<lang>\w*(-\w*)?)/$',
            non_admin_view(views.manual), name='manual'),
    re_path(r'^help/manual/(?P<lang>\w*(-\w*)?)/(?P<page>[\w-]+)$',
            non_admin_view(views.manual), name='manual-page'),
    re_path(r'^help/manual-download/$', non_admin_view(views.download_manual),
            name='download-manual'),
    re_path(r'^help/status-log/$', non_admin_view(views.status_log),
            name='status-log'),
]
