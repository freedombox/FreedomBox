"""FreedomBox app for implementing a OpenID Connect Provider.

With this app, FreedomBox implements a full OpenID Connect Provider along with
OpenID Discovery. Only authorization code grant type is currently supported but
can be easily extended to support other grant types if necessary. See this code
comment for quick understand of the flow works:
https://github.com/oauthlib/oauthlib/blob/master/oauthlib/oauth2/rfc6749/grant_types/authorization_code.py#L64

In the list of OpenID Connect claims provided to Relying Party, we override
django-oauth-toolkit's default 'sub' claim from being the user ID to username.
Additionally, we also provide basic profile information and 'freedombox_groups'
with list of all group names that the user account is part of.

"Clients" or "Applications": must be registered before they can be used with
the Identity Provider. Dynamic Client Registration is not supported yet. The
OpenIDConnect FreedomBox component will help with this registration.

Redirect URLs: After authorization is provided by the user, the URL of the
application to redirect to must be verified by the Identity Provider. This is
usually provided at the time of client registration. However, in FreedomBox,
since list of allowed domains keeps changing, the list of allowed redirect URLs
must keep changing as well. The OpenIDConnect component will also help with
that. Finally, there is overridden verification logic that ensures that
accessing protected applications using IP addresses or localhost domain names
in URLs is allowed.

The implement is done by implementing all the URLs in /freedombox/o. Most of
the implementation for these views and models is provided by
django-oauth-toolkit.
"""

import logging

from django.utils.translation import gettext_lazy as _

from plinth import app as app_module

from . import components

logger = logging.getLogger(__name__)


class OIDCApp(app_module.App):
    """FreedomBox app for OpenID Connect Provider."""

    app_id = 'oidc'

    _version = 1

    def __init__(self) -> None:
        """Create components for the app."""
        super().__init__()

        info = app_module.Info(app_id=self.app_id, version=self._version,
                               is_essential=True,
                               name=_('OpenID Connect Provider'))
        self.add(info)


def on_domain_added(sender: str, domain_type: str, name: str = '',
                    description: str = '',
                    services: str | list[str] | None = None, **kwargs):
    """Add domain to global list."""
    if not domain_type or not name:
        return

    logger.info('Updating all OpenID Connect components for domain add - %s',
                name)
    components.OpenIDConnect.update_domains_for_all()


def on_domain_removed(sender: str, domain_type: str, name: str = '', **kwargs):
    """Remove domain from global list."""
    if not domain_type or not name:
        return

    logger.info(
        'Updating all OpenID Connect components for domain remove - %s', name)
    components.OpenIDConnect.update_domains_for_all()
