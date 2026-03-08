# SPDX-License-Identifier: AGPL-3.0-or-later
"""Views for the Apache app."""

from urllib.parse import urlencode, urlparse

from django.http import (HttpResponseBadRequest, HttpResponseRedirect,
                         HttpResponseServerError)
from django.views import View

from . import setup_oidc_client, validate_host

# By default 'openid' scope already included by mod_auth_openidc
OIDC_SCOPES = 'email freedombox_groups'


class DiscoverIDPView(View):
    """A view called by auth_openidc Apache module to find the IDP.

    According to documentation for auth_openidc: an Issuer selection can be
    passed back to the callback URL as in:
    <callback-url>?iss=[${issuer}|${domain}|${e-mail-style-account-name}]
      [parameters][&login_hint=<login-hint>][&scopes=<scopes>]
      [&auth_request_params=<params>]

    where the <iss> parameter contains the URL-encoded issuer value of the
    selected Provider (or...), [parameters] contains the additional parameters
    that were passed in on the discovery request (e.g.
    target_link_uri=<url>&x_csrf=<x_csrf>&method=<method>&scopes=<scopes>)
    """

    def get(self, request):
        """Redirect back to auth_openidc module after selecting a IDP."""
        target_link_uri = request.GET.get('target_link_uri', '')
        method = request.GET.get('method', 'get')
        x_csrf = request.GET.get('x_csrf', '')
        oidc_callback = request.GET.get('oidc_callback')

        if method != 'get':
            return HttpResponseBadRequest(f'Cannot handle "{method}" method')

        oidc_callback_parts = urlparse(oidc_callback)
        request_host = request.get_host()
        if request_host != oidc_callback_parts.netloc:
            return HttpResponseBadRequest(
                f'Cannot redirect from {request_host} to a different host '
                f'{oidc_callback_parts.netloc}')

        try:
            validate_host(oidc_callback_parts.hostname)
        except ValueError:
            return HttpResponseBadRequest(
                f'Accessed using unknown domain {request_host}. Please add '
                'the domain to list of configured domains.')

        try:
            setup_oidc_client(oidc_callback_parts.netloc,
                              oidc_callback_parts.hostname)
        except ValueError:
            return HttpResponseServerError(
                f'Server not configured to called as {request_host}')

        url = '/apache/oidc/callback'
        params = {
            'iss': f'https://{request_host}/freedombox/o',
            'target_link_uri': target_link_uri,
            'method': method,
            'x_csrf': x_csrf,
            'scopes': OIDC_SCOPES,
        }
        params = urlencode(params)
        return HttpResponseRedirect(f'{url}?{params}')
