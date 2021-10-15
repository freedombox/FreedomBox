# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Utility methods for managing translations.
"""

from django.conf import settings
from django.utils import translation


def get_language_from_request(request):
    """Get the language in the session or as separate cookie.

    Django methods should be used for regular cases. This is only useful for
    very narrow cases.

    """
    if hasattr(request, 'session'):
        language_code = request.session.get(translation.LANGUAGE_SESSION_KEY)
        if language_code:
            return language_code

    return request.COOKIES.get(settings.LANGUAGE_COOKIE_NAME)


def set_language(request, response, language_code):
    """Set the language in session or as a separate cookie.

    Sending language code as None removes the preference. response is not
    optional as Django 3.0 up always set the language cookie and Django 4.0
    will no longer set the language in the session.

    """
    if not language_code:
        if hasattr(request, 'session'):
            try:
                del request.session[translation.LANGUAGE_SESSION_KEY]
            except KeyError:
                pass

        if response:
            try:
                response.delete_cookie(settings.LANGUAGE_COOKIE_NAME)
            except KeyError:
                pass

        return

    translation.activate(language_code)
    if hasattr(request, 'session'):
        request.session[translation.LANGUAGE_SESSION_KEY] = language_code

    response.set_cookie(
        settings.LANGUAGE_COOKIE_NAME,
        language_code,
        max_age=settings.LANGUAGE_COOKIE_AGE,
        path=settings.LANGUAGE_COOKIE_PATH,
        domain=settings.LANGUAGE_COOKIE_DOMAIN,
    )
