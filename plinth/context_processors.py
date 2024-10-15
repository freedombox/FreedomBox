# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Django context processors to provide common data to templates.
"""

import re

from django.utils.translation import gettext as _
from django.utils.translation import gettext_noop

from plinth import cfg, menu
from plinth.utils import is_user_admin


def common(request):
    """Add additional context values to RequestContext for use in templates.

    Any resources referenced in the return value are expected to have been
    initialized or configured externally beforehand.
    """
    # Allow a value in configuration file to be translated.  Allow
    # the brand name 'FreedomBox' itself to be translated.
    gettext_noop('FreedomBox')

    from plinth.notification import Notification
    notifications_context = Notification.get_display_context(
        request, user=request.user)

    slash_indices = [match.start() for match in re.finditer('/', request.path)]
    active_menu_urls = [
        request.path[:index + 1] for index in slash_indices[2:]
    ]  # Ignore the first two slashes '/plinth/apps/'
    return {
        'cfg': cfg,
        'active_menu_urls': active_menu_urls,
        'box_name': _(cfg.box_name),
        'user_is_admin': is_user_admin(request, True),
        'notifications': notifications_context['notifications'],
        'notifications_max_severity': notifications_context['max_severity']
    }
