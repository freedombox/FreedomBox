# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Django context processors to provide common data to templates.
"""

from django.utils.translation import gettext as _
from django.utils.translation import gettext_noop

from plinth import cfg, views, web_server
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

    breadcrumbs = views.get_breadcrumbs(request)
    active_section_url = [
        key for key, value in breadcrumbs.items()
        if value.get('is_active_section')
    ][0]
    return {
        'cfg': cfg,
        'breadcrumbs': breadcrumbs,
        'active_section_url': active_section_url,
        'box_name': _(cfg.box_name),
        'user_is_admin': is_user_admin(request, True),
        'user_css': web_server.get_user_css(),
        'notifications': notifications_context['notifications'],
        'notifications_max_severity': notifications_context['max_severity']
    }
