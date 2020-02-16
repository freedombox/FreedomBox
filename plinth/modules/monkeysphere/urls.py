# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the monkeysphere module.
"""

from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^sys/monkeysphere/$', views.index, name='index'),
    url(r'^sys/monkeysphere/(?P<ssh_fingerprint>[0-9A-Za-z:+/]+)/import/$',
        views.import_key, name='import'),
    url(r'^sys/monkeysphere/(?P<fingerprint>[0-9A-Fa-f]+)/details/$',
        views.details, name='details'),
    url(r'^sys/monkeysphere/(?P<fingerprint>[0-9A-Fa-f]+)/publish/$',
        views.publish, name='publish'),
    url(r'^sys/monkeysphere/cancel/$', views.cancel, name='cancel'),
]
