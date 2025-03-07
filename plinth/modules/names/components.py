# SPDX-License-Identifier: AGPL-3.0-or-later
"""
App component to introduce a new domain type.
"""

from typing import ClassVar

from django.utils.translation import gettext_lazy as _

from plinth import app

_SERVICES = {
    '__all__': {
        'display_name': _('All'),
        'port': None
    },
    'http': {
        'display_name': _('All web apps'),
        'port': 80
    },
    'https': {
        'display_name': _('All web apps'),
        'port': 443
    },
    'ssh': {
        'display_name': _('Secure Shell'),
        'port': 22
    },
}

list_type = list


class DomainType(app.FollowerComponent):
    """Component to create a new type of domain.

    It serves the primary purpose of showing a entry in the domain names page.
    This will allow users to discover the new type of domain and use the
    providing app to create that type of domain.

    Similar to a menu entry, domain type information is available to the user
    even when the corresponding app is disabled.

    """

    _all: ClassVar[dict[str, 'DomainType']] = {}

    def __init__(self, component_id: str, display_name: str,
                 configuration_url: str | None = None,
                 edit_url: str | None = None, delete_url: str | None = None,
                 add_url: str | None = None, can_have_certificate: bool = True,
                 priority: int = 50):
        """Initialize the domain type component.

        component_id should be a unique ID across all components of an app and
        across all components. This will also act as the 'type' parameter for
        each created domain.

        display_name is the type of domain displayed to the user in the
        interface.

        configuration_url is the Django URL to which a user is redirected to in
        order to create or manage a domain of this type.

        edit_url is the Django URL to which a user is redirected to in order to
        edit a particular domain of this type. A keyword argument 'domain' is
        passed when reversing this URL.

        delete_url is the Django URL to which a user is redirected to in order
        to delete a particular domain of this type. A keyword argument 'domain'
        is passed when reversing this URL.

        add_url is the Django URL to which a user is redirected to in order to
        add a particular domain of this type.

        can_have_certificate indicates if this type of domain can have a TLS
        certificate that can be validated by a typical browser.

        priority decides which domain will be used (by default) when an app can
        only deal with a single domain. The domain with highest value will be
        chosen by the app by default.
        """
        super().__init__(component_id)

        self.display_name = display_name
        self.configuration_url = configuration_url
        self.edit_url = edit_url
        self.delete_url = delete_url
        self.add_url = add_url
        self.can_have_certificate = can_have_certificate
        self.priority = priority

        self._all[component_id] = self

    @classmethod
    def get(cls, component_id: str) -> 'DomainType':
        """Return a component of given ID."""
        return cls._all[component_id]

    @classmethod
    def list(cls) -> dict[str, 'DomainType']:
        """Return a list of all domain types."""
        sorted_items = sorted(cls._all.items(),
                              key=lambda item: item[1].priority, reverse=True)
        domain_types = {key: value for key, value in sorted_items}
        return domain_types


class DomainName(app.FollowerComponent):
    """Component to represent a domain name and its properties.

    Each domain name is necessarily attached to a domain type component that
    must be created prior to creating the domain name.

    When an application providing or managing a domain name is disabled, the
    corresponding domain name should become unavailable for others apps and
    they must de-configure the domain name from app configuration. This is the
    primary reason for making a domain name available as a component.

    """
    _all: ClassVar[dict[str, 'DomainName']] = {}

    def __init__(self, component_id: str, name: str, domain_type: str,
                 services: list[str] | str):
        """Initialize a domain name.

        component_id should be a unique ID across all components of an app and
        across all components. The value is typically 'domain-{app}-{domain}'.
        This ensures that if the same domain is managed by multiple apps, it is
        available as multiple instances. When one instance is removed, say by
        disabling that app, the other instance will still provide that domain.

        name is the domain name that is being represented by the component.
        This should be fully qualified domain name.

        domain_type should be a string representing the type of the domain.
        This is the component ID of the domain type earlier registered by the
        app that is creating the domain name component.

        services is a list of string identifiers for services potentially
        provided by the domain. For example, 'ssh' for secure shell service
        provided on port 22. It is used for showing information to the user and
        to retrieve a list of a domains that an app may use.

        A service value can also be an integer in which case it will be
        converted to a string by looking up a list of known services. This
        process is not perfect and may cause problems when filtering domains
        that could potentially provide a service.

        The most common value of a services parameter is the string '__all__'
        indicating that the domain can potentially provide any service without
        limitations due to the nature of the domain name.

        """
        super().__init__(component_id)

        self.name = name
        self.domain_type = DomainType.get(domain_type)
        self._services = DomainName._normalize_services(services)

        self._all[component_id] = self

    @property
    def services(self):
        """Read-only property to get the list of services."""
        return self._services

    @staticmethod
    def _normalize_services(services):
        """If ports numbers are provided convert them to service IDs."""
        if services == '__all__':
            return services

        return [DomainName._normalize_service(service) for service in services]

    @staticmethod
    def _normalize_service(service):
        """Return the service ID for a given port number.

        XXX: Eliminate this and use a generalized approach eventually.
        """
        if isinstance(service, str):
            return service

        if not isinstance(service, int):
            raise ValueError('Invalid service')

        for service_id, description in _SERVICES.items():
            if description['port'] == service:
                return service_id

        return str(service)

    def get_readable_services(self) -> set[str]:
        """Return list of unique service strings that can be shown to user."""
        services = self.services
        if self.services == '__all__':
            services = [services]

        return {
            _SERVICES.get(service, {'display_name': service})['display_name']
            for service in services
        }

    def has_service(self, service: str | None) -> bool:
        """Return whether a service is available for this domain name."""
        return (service is None or self.services == '__all__'
                or service in self.services)

    def remove(self) -> None:
        """Remove the domain name from global list of domains.

        It is acceptable to call remove() multiple times.
        """
        try:
            del self._all[self.component_id]
        except KeyError:
            pass

    @classmethod
    def get(cls, component_id):
        """Return the domain name object given name and app."""
        return cls._all[component_id]

    @classmethod
    def list(cls,
             filter_for_service: str | None = None) -> list_type['DomainName']:
        """Return list of domains sorted by importance.

        Domains are first sorted by priority with higher values showing up
        first and then by their domain name.
        """
        domains = [
            domain for domain in cls._all.values()
            if domain.has_service(filter_for_service)
        ]
        return sorted(
            domains, key=lambda domain:
            (-domain.domain_type.priority, domain.name))

    @classmethod
    def list_names(cls,
                   filter_for_service: str | None = None) -> list_type[str]:
        """Return a set of unique domain names.

        Domains are first sorted by priority with higher values showing up
        first and then by their domain name.

        Multiple different components may provide the same domain name. This
        method could be used to retrieve a list of all domain names without
        duplication.
        """
        domain_names: dict[str, bool] = {}
        for domain in cls.list(filter_for_service):
            domain_names[domain.name] = True

        return list(domain_names.keys())
