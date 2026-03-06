# SPDX-License-Identifier: AGPL-3.0-or-later
"""App component for other apps to authenticate with OpenID Connect."""

from plinth import app as app_module


class OpenIDConnect(app_module.FollowerComponent):
    """Component to authentication with OpenID Connection."""

    def __init__(self, component_id: str, client_id: str, name: str,
                 redirect_uris: list[str], skip_authorization: bool = False):
        """Initialize the OpenID Connect component.

        name is a description name for the client that is only used for record
        keeping.

        client_id is ID to use when registring the app as client (relying
        party) with FreedomBox's OpenID Connect Provider.

        redirect_uris is list of string containing URIs that the user's agent
        may be redirected to after successful authentication. If the URIs
        contain {domain} in their string, it will be expanded to the list of
        all domains configured in FreedomBox.
        """
        super().__init__(component_id)

        self.client_id = client_id
        self.name = name
        self.redirect_uris = redirect_uris
        self.post_logout_redirect_uris = ''  # None is not allowed
        self._client_type = None
        self._authorization_grant_type = None
        self._algorithm = None
        self.hash_client_secret = False
        self.skip_authorization = skip_authorization

    @property
    def client_type(self):
        """Return the client type.

        This is a property instead of a simple attribute to avoid importing
        Application model during component.__init__(). This would require
        Django to be configured.
        """
        from oauth2_provider.models import Application
        return self._client_type or Application.CLIENT_CONFIDENTIAL

    @client_type.setter
    def client_type(self, value):
        """Set the client type."""
        self._client_type = value

    @property
    def authorization_grant_type(self):
        """Return the authorization grant type.

        This is a property instead of a simple attribute to avoid importing
        Application model during component.__init__(). This would require
        Django to be configured.
        """
        from oauth2_provider.models import Application
        return (self._authorization_grant_type
                or Application.GRANT_AUTHORIZATION_CODE)

    @authorization_grant_type.setter
    def authorization_grant_type(self, value):
        """Set the authorization grant type."""
        self._authorization_grant_type = value

    @property
    def algorithm(self):
        """Return the algorithm.

        This is a property instead of a simple attribute to avoid importing
        Application model during component.__init__(). This would require
        Django to be configured.
        """
        from oauth2_provider.models import Application
        return self._algorithm or Application.HS256_ALGORITHM

    @algorithm.setter
    def algorithm(self, value):
        """Set the algorithm."""
        self._algorithm = value

    def get_client_secret(self):
        """Return the client secret stored for the application."""
        from oauth2_provider.models import Application
        return Application.objects.get_by_natural_key(
            self.client_id).client_secret

    def setup(self, old_version: int) -> None:
        """Register the app as client."""
        self._create_or_update_application()

    @staticmethod
    def update_domains_for_all():
        """For all app components, update redirect URIs and allowed origins."""
        for app in app_module.App.list():
            for component in app.components.values():
                if isinstance(component, OpenIDConnect):
                    component._create_or_update_application()

    def _create_or_update_application(self) -> None:
        """Register the app as client."""
        from oauth2_provider.models import Application
        try:
            application = Application.objects.get_by_natural_key(
                self.client_id)
            self._update_application(application)
        except Application.DoesNotExist:
            self._create_application()

    def _create_application(self) -> None:
        """Create a new application object."""
        from oauth2_provider import generators
        from oauth2_provider.models import Application
        client_secret = generators.generate_client_secret()
        Application.objects.create(
            client_id=self.client_id, client_secret=client_secret, user=None,
            redirect_uris=self._get_redirect_uris(),
            post_logout_redirect_uris=self.post_logout_redirect_uris,
            client_type=self.client_type,
            authorization_grant_type=self.authorization_grant_type,
            hash_client_secret=self.hash_client_secret, name=str(self.name),
            algorithm=self.algorithm,
            allowed_origins=self._get_allowed_origins(),
            skip_authorization=self.skip_authorization)

    def _update_application(self, application) -> None:
        """Update configuration for an existing application."""
        application.user = None
        application.redirect_uris = self._get_redirect_uris()
        application.post_logout_redirect_uris = self.post_logout_redirect_uris
        application.client_type = self.client_type
        application.authorization_grant_type = self.authorization_grant_type
        application.hash_client_secret = self.hash_client_secret
        application.name = str(self.name)
        application.algorithm = self.algorithm
        application.allowed_origins = self._get_allowed_origins()
        application.skip_authorization = self.skip_authorization
        application.save()

    def _get_redirect_uris(self) -> str:
        """Return an expanded list of redirect URIs."""
        from plinth.modules.names.components import DomainName
        final_uris = []
        # redirect_uris list can't be empty. Otherwise, validations for
        # 'localhost' and IP addresses won't work.
        domains = set(DomainName.list_names()) | {'localhost'}
        for uri in self.redirect_uris:
            if '{domain}' in uri:
                for domain in domains:
                    final_uris.append(uri.format(domain=domain))
            else:
                final_uris.append(uri)

        return ' '.join(final_uris)

    def _get_allowed_origins(self) -> str:
        """Return a list of all allowed origins for CORS header."""
        from plinth.modules.names.components import DomainName

        # redirect_uris list can't be empty. Otherwise, validations for
        # 'localhost' and IP addresses won't work. Keep origins in line with
        # redirect_uris.
        domains = set(DomainName.list_names()) | {'localhost'}
        origins = [f'https://{domain_name}' for domain_name in domains]
        return ' '.join(origins)
