"""Custom OpenID Connect validators."""

import ipaddress
import urllib.parse

from oauth2_provider import oauth2_validators

from plinth import action_utils


class OAuth2Validator(oauth2_validators.OAuth2Validator):
    """Add/override claims into Discovery and ID token.

    Ensure that basic profile information is available to the clients. Make the
    value of the 'sub' claim, as defined in OpenID Connect, to be the username
    of the account instead of the Django account ID. The username is unique in
    FreedomBox.

    We wish for the applications using the Identity Provider to also
    provide/deny resources based on the groups that the user is part of. For
    this, we add an additional scope "freedombox_groups" and additional claim
    "freedombox_groups". To define custom scopes and claims, we need to ensure
    that the keys used are unique and will not clash with other
    implementations. 'freedombox_' prefix seems reasonable. The value of this
    claim is a list of all groups that the user account is part of.
    """

    # Add a scope, as recommended in the oauth-toolkit documentation.
    oidc_claim_scope = oauth2_validators.OAuth2Validator.oidc_claim_scope
    oidc_claim_scope.update({'freedombox_groups': 'freedombox_groups'})

    def get_additional_claims(self):
        """Override value of 'sub' claim and add other claims.

        Only the 'sub' claim is filled by default by django-oauth-toolkit. The
        rest, as needed, must be filled by us.

        Use the 'second' form of get_additional_claims override as
        documentation suggests so that the base code and automatically add the
        list of claims returned here to list of supported claims.
        """

        def _get_user_groups(request):
            return list(request.user.groups.values_list('name', flat=True))

        return {
            'sub': lambda request: request.user.username,
            'email': lambda request: request.user.email,
            'preferred_username': lambda request: request.user.username,
            'freedombox_groups': _get_user_groups,
        }

    def validate_redirect_uri(self, client_id, redirect_uri, request, *args,
                              **kwargs):
        """Additionally allow redirection to this server's IPs and domains."""
        allowed_redirect_uris = request.client.redirect_uris.split()
        if _validate_local_domains_and_ips(redirect_uri, request,
                                           allowed_redirect_uris):
            return True

        return super().validate_redirect_uri(client_id, redirect_uri, request,
                                             *args, **kwargs)


def _validate_local_domains_and_ips(redirect_uri, request,
                                    allowed_redirect_uris):
    """Allow redirect to local domains and IPs.

    See models.py:redirect_to_uri_allowed() in django-oauth-toolkit for
    reference.

    Path and query part of the redirect URL must always match with one of the
    configured redirect URLs for this application. The query in the redirect
    URI is allowed to be a subset of the allowed query.

    Localhost domains (localhost, ip6-localhost, and ip6-loopback) are allowed
    in redirect URLs. Scheme and port are not checked.

    An IP address based redirect URL is accepted as long as it is to the same
    IP address with which the FreedomBox's Identity Provider is being accessed.
    Scheme is not checked. Changing IP address during OpenID Connect flow is
    not allowed.
    """
    # Requires 'ProxyPreserveHost On' in Apache2 configuration for proxying
    # requests to FreedomBox service.
    request_host = request.headers.get('HTTP_HOST')

    parsed_redirect_uri = urllib.parse.urlparse(redirect_uri)

    redirect_uri_query_set = set(
        urllib.parse.parse_qs(parsed_redirect_uri.query))
    try:
        ipaddress.ip_address(parsed_redirect_uri.hostname)
        redirect_uri_is_ip = True
    except ValueError:
        redirect_uri_is_ip = False

    redirect_uri_is_localhost = parsed_redirect_uri.hostname in (
        'localhost', 'ip6-localhost', 'ip6-loopback',
        action_utils.get_hostname())

    for allowed_uri in allowed_redirect_uris:
        parsed_allowed_uri = urllib.parse.urlparse(allowed_uri)

        # Path must match one of the allowed paths
        if parsed_redirect_uri.path != parsed_allowed_uri.path:
            continue

        # Query must be a subset of allowed query
        allowed_query_set = set(urllib.parse.parse_qs(
            parsed_allowed_uri.query))
        if not allowed_query_set.issubset(redirect_uri_query_set):
            continue

        # If the redirect is to an IP address, it is only allowed if the IDP
        # itself is being accessed with that IP address.
        if (redirect_uri_is_ip and request_host
                and parsed_redirect_uri.netloc == request_host):
            return True

        # If the redirect is to a 'localhost' like address, a port mismatch is
        # allowed.
        if redirect_uri_is_localhost:
            return True

    return False  # Special criteria didn't match, do usual checks.
