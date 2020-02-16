# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the Secure Shell Server module.
"""

from django.conf.urls import url

from plinth.modules.ssh.views import SshAppView

urlpatterns = [
    url(r'^sys/ssh/$', SshAppView.as_view(), name='index'),
]
