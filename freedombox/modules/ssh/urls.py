# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the Secure Shell Server module.
"""

from django.urls import re_path

from plinth.modules.ssh.views import SshAppView

urlpatterns = [
    re_path(r'^sys/ssh/$', SshAppView.as_view(), name='index'),
]
