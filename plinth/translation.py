#
# This file is part of FreedomBox.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
"""
Utility methods for managing translations.
"""

from django.conf import settings
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
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

    Sending language code as None removes the preference. If response is None,
    cookies are not touched and setting/deleting language cookie will not work.

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
    else:
        response.set_cookie(
            settings.LANGUAGE_COOKIE_NAME,
            language_code,
            max_age=settings.LANGUAGE_COOKIE_AGE,
            path=settings.LANGUAGE_COOKIE_PATH,
            domain=settings.LANGUAGE_COOKIE_DOMAIN,
        )


@receiver(user_logged_in)
def _on_user_logged_in(sender, request, user, **kwargs):
    """When the user logs in, set the current language."""
    set_language(request, None, user.userprofile.language)
