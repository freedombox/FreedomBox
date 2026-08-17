# SPDX-License-Identifier: AGPL-3.0-or-later
"""URLs for the OpenID Connect module.

All the '/freedombox/o' URLs are implemented in this module by including them
from django-oauth-toolkit. However, they are included in plinth/urls.py instead
of here because FreedomBox module loading logic automatically namespaces the
URL names. This causes problems when metadata view tries to resolve URLs.

/.well-known/openid-configuration is proxied to
/freedombox/o/.well-known/openid-configuration by Apache2. Similarly,
/.well-known/jwks.json is proxied to /freedombox/o/.well-known/jwks.json.

Important URLs:

- /freedombox/o is the primary URL for identity provider.

- /freedombox/o/.well-known/openid-configuration is the way to discover
additional URLs (such as ./authorize and ./token) needed for OIDC to work.

- /freedombox/o/authorize is used to start the authorization process and get an
authorization code grant.

- /freedombox/o/token is used to get access token and refresh token using the
authorization code. It is also used to get a new access token using the refresh
token.

- /freedombox/o/userinfo provides the claims such as 'sub', 'email',
'freedombox_groups' using an access token.
"""

urlpatterns: list = []
