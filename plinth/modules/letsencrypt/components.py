# SPDX-License-Identifier: AGPL-3.0-or-later
"""App component for other apps to use handle Let's Encrypt certificates."""

import logging
import pathlib
import threading
from typing import ClassVar

from plinth import app
from plinth.modules.names.components import DomainName
from plinth.privileged import service as service_privileged

from . import privileged

logger = logging.getLogger(__name__)

_list_type = list


class LetsEncrypt(app.FollowerComponent):
    """Component to receive Let's Encrypt renewal hooks.

    Performs the following tasks:

    - Listen to certificate change events from the Let's Encrypt app. This
      could be obtain, re-obtain, renewal, revoke and delete events.

    - Filter out events after comparing domains list in certificate events to
      the list of domains the app (to which this component belongs) is
      interested in.

    - If requested, copy certificates from /etc/letsencrypt directory to app's
      directory with the needed permissions and ownership.

    - Query status of copied certificates. Status could be up-to-date,
      self-signed, outdated (/etc/letsencrypt has more recent certificate),
      expired or a test certificate.

    - Optionally restart a bunch of daemons after interesting certificate event
      occurs.

    """

    _all: ClassVar[dict[str, 'LetsEncrypt']] = {}

    def __init__(self, component_id, domains=None, daemons=None,
                 should_copy_certificates=False, private_key_path=None,
                 certificate_path=None, user_owner=None, group_owner=None,
                 managing_app=None, reload_daemons=False):
        """Initialize the Let's Encrypt component.

        component_id should be a unique ID across all components of an app and
        across all components.

        domains is a list of domains that the app is configured for. Any
        certificate operation that is not happening on these domains is ignored
        by this component.

        domains can be the string '*' in which case it means that the app is
        relevant for (or is interested in) all domains configured in the
        system.

        domains can be a callable instead of a list. In this case, the callable
        is called every time an operation needs to be checked against list of
        domains for the app. The callable must return a list of domains that
        the app is configured for.

        daemons is a list of systemd units that need to be restarted (actually
        try-restarted, i.e., only if they are already running) when a relevant
        certificate operation happens.

        should_copy_certificates indicates whether the app needs the Let's
        Encrypt certificates in the directory /etc/letsencrypt to be copied to
        a different location with different permissions to be able to use them.
        If true, private_key_path, certificate_path, user_owner, group_owner
        and managing_app properties must be specified. Otherwise, ValueError is
        raised.

        private_key_path is the string containing the file path to which a
        private key must be copied. It may contain the sub-string '{domain}'
        which will be replaced with the name of the domain for which this
        certificate is being copied. Any non-existing parent directories are
        created with 'root:root' ownership and '0o755' file permissions. The
        permissions for the file will be '0o600' and ownership will be as
        specified in parameters user_owner and group_owner. If both
        private_key_path and certificate_path refer to the same path, the
        target file is created by appending the private key and certificate.

        certificate_path is the string containing the file path to which a
        certificate must be copied. It may contain the sub-string '{domain}'
        which will be replaced with the name of the domain for which this
        certificate is being copied. Any non-existing parent directories are
        created with 'root:root' ownership and '0o755' file permissions. The
        permissions for the file will be '0o644' and ownership will be as
        specified in parameters user_owner and group_owner. If both
        private_key_path and certificate_path refer to the same path, the
        target file is created by appending the private key and certificate.

        user_owner specifies the user who should own the copied certificates.
        This is typically the unprivileged user account that runs the daemon.

        group_owner specifies the group who should own the copied certificates.
        This is typically the unprivileged group account that runs the daemon.

        managing_app is the name of the app that contains this component. This
        is used by the superuser action to verify that this app is allowed to
        copy certificates to the target location. The app must then define a
        property 'managing_paths' which contains a list of pathlib.Path()
        objects to which the app is allowed to write certificates and other
        files to.

        reload_daemons is boolean to indicate if the daemons should be reloaded
        instead of restarted (which is default).
        """
        if should_copy_certificates:
            if (not private_key_path or not certificate_path or not user_owner
                    or not group_owner or not managing_app):
                raise ValueError('Not enough values for copying certificates')

        super().__init__(component_id)
        self._domains = domains
        self.daemons = daemons
        self.reload_daemons = reload_daemons
        self.should_copy_certificates = should_copy_certificates
        self.private_key_path = private_key_path
        self.certificate_path = certificate_path
        self.user_owner = user_owner
        self.group_owner = group_owner
        self.managing_app = managing_app

        self._all[component_id] = self

    @property
    def domains(self) -> list[str] | str:
        """Return a list of domains this component's app is interested in."""
        if callable(self._domains):
            return self._domains()

        return self._domains

    @classmethod
    def list(cls):
        """Return a list of all Let's Encrypt components."""
        return cls._all.values()

    def setup_certificates(
            self, app_domains: str | _list_type[str] | None = None) -> None:
        """Setup app certificates for all interested domains.

        For every domain, a certificate is copied. If a valid certificate is
        not available in Let's Encrypt, a self-signed snakeoil certificate is
        used. Each daemon is restarted if it is running.

        app_domains is the list of domains for which certificates must be
        copied. If it is not provided, the component's list of domains (which
        may be acquired by a callable) is used.
        """
        if not app_domains:
            app_domains = self.domains

        if app_domains == '*':
            # Setup for all domains and not just ones that LE can obtain
            # certificate for. This allows the domains that can't have LE
            # certificate to work with self-signed certificates.
            app_domains = DomainName.list_names()

        domains, status = self._get_letsencrypt_domains()

        if self.should_copy_certificates:
            for domain in app_domains:
                if domain in domains:
                    lineage = status['domains'][domain]['lineage']
                    self._copy_letsencrypt_certificates([domain], lineage)
                else:
                    self._copy_self_signed_certificates([domain])

        for daemon in self.daemons:
            if self.reload_daemons:
                service_privileged.try_reload_or_restart(daemon)
            else:
                service_privileged.try_restart(daemon)

    def get_status(self):
        """Return the status of certificates for all interested domains.

        A dictionary is returned containing a key for each domain and the value
        shall be a simple string with state of certificate for this app.
        Possible values are 'outdated-copy', 'self-signed', 'unknown', 'valid',
        'revoked', 'expired' and 'test_cert'.

        """
        app_domains = self.domains
        domains, le_status = self._get_letsencrypt_domains()

        final_status = {}
        for domain in app_domains:
            if domain in domains:
                status = le_status['domains'][domain]['validity']
                if self.should_copy_certificates:
                    if not self._compare_certificate(
                            domain, le_status['domains'][domain]['lineage']):
                        status = 'outdated-copy'
            else:
                status = 'self-signed'

            final_status[domain] = status

        return final_status

    def on_certificate_obtained(self, domains, lineage):
        """Handle event when a certificate is obtained.

        Filter any domains that are interesting for the app that this component
        is part of. For all interesting domains, copy the certificates if
        requested and then restart the daemons.

        """
        interested_domains = self._get_interested_domains(domains)
        if not interested_domains:
            return

        if self.should_copy_certificates:
            self._copy_letsencrypt_certificates(interested_domains, lineage)

        for daemon in self.daemons:
            if self.reload_daemons:
                service_privileged.try_reload_or_restart(daemon)
            else:
                service_privileged.try_restart(daemon)

    def on_certificate_renewed(self, domains, lineage):
        """Handle event when a certificate is renewed.

        This is typically called when a Cron job triggers certbot renewal
        process which in turn triggers configured renewal hooks after
        successful renewal. It is also called when a valid certificate is
        re-obtained.

        To trigger a renewal event for testing purposes, run `certbot renew
        --force-renewal`.

        For now, performs the same operations as obtaining a fresh certificate.

        """
        return self.on_certificate_obtained(domains, lineage)

    def on_certificate_revoked(self, domains, lineage):
        """Handle event when a certificate is revoked.

        Filter any domains that are interesting for the app that this component
        is part of. For all interesting domains, copy self-signed snakeoil
        certificates if requested and then restart the daemons.

        """
        interested_domains = self._get_interested_domains(domains)
        if not interested_domains:
            return

        if self.should_copy_certificates:
            self._copy_self_signed_certificates(interested_domains)

        for daemon in self.daemons:
            if self.reload_daemons:
                service_privileged.try_reload_or_restart(daemon)
            else:
                service_privileged.try_restart(daemon)

    def on_certificate_deleted(self, domains, lineage):
        """Handle event when a certificate is deleted.

        For now, performs the same operations as obtaining a fresh certificate.

        """
        return self.on_certificate_revoked(domains, lineage)

    @staticmethod
    def _get_letsencrypt_domains():
        """Return the list of domains with LE certificates."""
        from plinth.modules import letsencrypt
        status = letsencrypt.get_status()
        domains = {
            domain
            for domain, domain_status in status['domains'].items()
            if domain_status
        }
        return domains, status

    def _get_interested_domains(self, domains):
        """Return set of domains the component is interested in."""
        app_domains = self.domains
        if not app_domains:
            return set()

        if app_domains == '*':
            return set(domains)

        return set(domains).intersection(set(app_domains))

    def _copy_self_signed_certificates(self, domains):
        """Copy a self-signed certificate for all domains.

        Copy Apache's snake-oil certificate into daemon's directory. The
        self-signed certificate may not really work. It is merely to prevent
        the server from failing to startup because the files are missing.

        """
        source_private_key_path = '/etc/ssl/private/ssl-cert-snakeoil.key'
        source_certificate_path = '/etc/ssl/certs/ssl-cert-snakeoil.pem'
        self._copy_certificates(domains, source_private_key_path,
                                source_certificate_path)

    def _copy_letsencrypt_certificates(self, domains, lineage):
        """Copy a valid Let's Encrypt certificate for given domains."""
        source_private_key_path = pathlib.Path(lineage) / 'privkey.pem'
        source_certificate_path = pathlib.Path(lineage) / 'fullchain.pem'
        self._copy_certificates(domains, source_private_key_path,
                                source_certificate_path)

    def _copy_certificates(self, domains, source_private_key_path,
                           source_certificate_path):
        """Copy certificate for all domains in the certificate.

        The list of domains passed should be subset of domains listed in the
        certificate.

        """
        if '{domain}' in self.private_key_path or \
           '{domain}' in self.certificate_path:
            for domain in domains:
                private_key_path = self.private_key_path.format(domain=domain)
                certificate_path = self.certificate_path.format(domain=domain)
                self._copy_certificate(source_private_key_path,
                                       source_certificate_path,
                                       private_key_path, certificate_path)
        else:
            self._copy_certificate(source_private_key_path,
                                   source_certificate_path,
                                   self.private_key_path,
                                   self.certificate_path)

    def _copy_certificate(self, source_private_key_path,
                          source_certificate_path, private_key_path,
                          certificate_path):
        """Copy certificate for a single domain."""
        privileged.copy_certificate(self.managing_app,
                                    str(source_private_key_path),
                                    str(source_certificate_path),
                                    private_key_path, certificate_path,
                                    self.user_owner, self.group_owner)

    def _compare_certificate(self, domain, lineage):
        """Compare LE certificate with app certificate."""
        source_private_key_path = pathlib.Path(lineage) / 'privkey.pem'
        source_certificate_path = pathlib.Path(lineage) / 'fullchain.pem'
        private_key_path = self.private_key_path.format(domain=domain)
        certificate_path = self.certificate_path.format(domain=domain)
        return privileged.compare_certificate(self.managing_app,
                                              str(source_private_key_path),
                                              str(source_certificate_path),
                                              private_key_path,
                                              certificate_path)


def on_certificate_event(event, domains, lineage):
    """Start a new thread to handle a LE certificate event.

    Run in a new thread because:

    - We don't want to block the thread running Glib main loop when called from
      dbus handler in case of renewal.

    - We don't want to delay the a certificate operation with copying
      certificates to all apps.

    - We don't want to cause a page load error when restarting Apache due to
      certificate changes.

    """
    threading.Thread(target=on_certificate_event_sync,
                     args=(event, domains, lineage)).start()


def on_certificate_event_sync(event, domains, lineage):
    """Trigger certificate event hooks across all apps."""
    if isinstance(domains, str):
        domains = domains.split()

    if not lineage:
        # XXX: A better to find lineage is by reading the renewal/{domain}.conf
        lineage = str(pathlib.Path('/etc/letsencrypt/live/') / domains[0])

    assert event in ('obtained', 'renewed', 'revoked', 'deleted')

    for component in LetsEncrypt.list():
        logger.info('Handling certificate event for %s: %s, %s, %s',
                    component.component_id, event, domains, lineage)
        try:
            getattr(component, 'on_certificate_' + event)(domains, lineage)
        except Exception as exception:
            logger.exception(
                'Error executing certificate hook for %s: %s, %s, %s: %s',
                component.component_id, event, domains, lineage, exception)

    if event in ('obtained', 'renewed'):
        from plinth.modules import letsencrypt
        letsencrypt.certificate_set_last_seen_modified_time(lineage)
