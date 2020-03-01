# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the Help module
"""

from django.conf.urls import url

from plinth.utils import non_admin_view

from . import views

urlpatterns = [
    url(r'^help/$', non_admin_view(views.index), name='index'),
    url(r'^help/about/$', non_admin_view(views.about), name='about'),
    url(r'^help/feedback/$', non_admin_view(views.feedback), name='feedback'),
    url(r'^help/support/$', non_admin_view(views.support), name='support'),
    url(r'^help/contribute/$', non_admin_view(views.contribute),
        name='contribute'),
    url(r'^help/manual/$', non_admin_view(views.manual), name='manual'),
    url(r'^help/manual/(?P<lang>\w*(-\w*)?)/$', non_admin_view(views.manual),
        name='manual'),
    url(r'^help/manual/(?P<lang>\w*(-\w*)?)/(?P<page>[\w-]+)$',
        non_admin_view(views.manual), name='manual-page'),
    url(r'^help/manual-download/$', non_admin_view(views.download_manual),
        name='download-manual'),
    url(r'^help/status-log/$', non_admin_view(views.status_log),
        name='status-log'),
]
