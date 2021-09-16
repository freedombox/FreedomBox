# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the monkeysphere module.
"""

from django.urls import re_path

from . import views

urlpatterns = [
    re_path(r'^sys/monkeysphere/$', views.index, name='index'),
    re_path(r'^sys/monkeysphere/(?P<ssh_fingerprint>[0-9A-Za-z:+/]+)/import/$',
            views.import_key, name='import'),
    re_path(r'^sys/monkeysphere/(?P<fingerprint>[0-9A-Fa-f]+)/details/$',
            views.details, name='details'),
    re_path(r'^sys/monkeysphere/(?P<fingerprint>[0-9A-Fa-f]+)/publish/$',
            views.publish, name='publish'),
    re_path(r'^sys/monkeysphere/cancel/$', views.cancel, name='cancel'),
]
