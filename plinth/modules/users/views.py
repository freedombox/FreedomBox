# SPDX-License-Identifier: AGPL-3.0-or-later
"""Django views for user app."""

import functools
import importlib.metadata
import json
import logging
import re
import uuid

import axes.utils
import django.views.generic
import fido2.cbor
import fido2.features
import fido2.utils
from django import shortcuts
from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView as DjangoLoginView
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy
from django.views.decorators.http import require_POST
from django.views.generic.edit import (CreateView, DeleteView, FormView,
                                       UpdateView)
from fido2 import webauthn
from fido2.server import Fido2Server
from fido2.webauthn import AttestedCredentialData, AuthenticationResponse

import plinth.modules.ssh.privileged as ssh_privileged
from plinth import translation
from plinth.models import UserPasskey
from plinth.modules import first_boot
from plinth.utils import is_user_admin
from plinth.version import Version
from plinth.views import AppView, json_exception

from . import privileged
from .forms import (AuthenticationForm, CaptchaForm, CreateUserForm,
                    FirstBootForm, UserChangePasswordForm, UserUpdateForm)

# Enable fido2 basic features
if Version(importlib.metadata.version('fido2')) < Version('2.0.0'):
    fido2.features.webauthn_json_mapping.enabled = True  # type: ignore

logger = logging.getLogger(__name__)


class LoginView(DjangoLoginView):
    """View to login to FreedomBox and set language preference."""

    redirect_authenticated_user = True
    template_name = 'users_login.html'
    form_class = AuthenticationForm

    def dispatch(self, request, *args, **kwargs):
        """Handle a request and return a HTTP response."""
        response = super().dispatch(request, *args, **kwargs)
        if request.user.is_authenticated:
            translation.set_language(request, response,
                                     request.user.userprofile.language)

        return response


class CaptchaView(FormView):
    """A simple form view with a CAPTCHA image.

    When a user performs too many login attempts, they will no longer be able
    to login with the typical login view. They will be redirected to this view.
    On successfully solving the CAPTCHA in this form, their ability to use the
    login form will be reset.
    """

    template_name = 'users_captcha.html'
    form_class = CaptchaForm

    def form_valid(self, form):
        """Reset login attempts and redirect to login page."""
        axes.utils.reset_request(self.request)
        return shortcuts.redirect('users:login')


@require_POST
def logout(request):
    """Logout an authenticated user, remove SSO cookie and redirect to home."""
    auth_logout(request)
    response = shortcuts.redirect('index')

    # HACK: Remove Apache OpenID Connect module's session. This will logout all
    # the apps using mod_auth_openidc for their authentication and
    # authorization. A better way to do this is to implement OpenID Connect's
    # Back-Channel Logout[1] or using OpenID Connect Session Management[2].
    # With this scheme, each application will register a logout URL during
    # client registration. The OpenID Provider (FreedomBox service) will call
    # this URL with appropriate parameters to perform logout on all the apps.
    # Support for OpenID Connect Back-Channel Logout is currently under
    # review[3].
    # 1. https://openid.net/specs/openid-connect-backchannel-1_0.html
    # 2. https://openid.net/specs/openid-connect-session-1_0.html
    # 3. https://github.com/django-oauth/django-oauth-toolkit/pull/1573
    response.delete_cookie('mod_auth_openidc_session')

    messages.success(request, _('Logged out successfully.'))
    return response


class ContextMixin:
    """Mixin to add 'title' to the template context."""

    def get_context_data(self, **kwargs):
        """Add self.title to template context."""
        context = super().get_context_data(**kwargs)
        context['title'] = getattr(self, 'title', '')
        return context


class UserCreate(ContextMixin, SuccessMessageMixin, CreateView):
    """View to create a new user."""

    form_class = CreateUserForm
    template_name = 'users_create.html'
    model = User
    success_message = gettext_lazy('User %(username)s created.')
    success_url = reverse_lazy('users:create')
    title = gettext_lazy('Create User')

    def get_form_kwargs(self):
        """Make the request object available to the form."""
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_success_url(self):
        """Return the URL to redirect to in case of successful updation."""
        return reverse('users:index')


class UserList(AppView, ContextMixin, django.views.generic.ListView):
    """View to list users."""

    model = User
    template_name = 'users_list.html'
    title = gettext_lazy('Users')
    app_id = 'users'


class UserUpdate(ContextMixin, SuccessMessageMixin, UpdateView):
    """View to update a user's details."""

    template_name = 'users_update.html'
    model = User
    form_class = UserUpdateForm
    slug_field = 'username'
    success_message = gettext_lazy('User %(username)s updated.')
    title = gettext_lazy('Edit User')

    def dispatch(self, request, *args, **kwargs):
        """Handle a request and return a HTTP response."""
        if self.request.user.get_username() != self.kwargs['slug'] \
                and not is_user_admin(self.request):
            raise PermissionDenied

        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        """Make the request object available to the form."""
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        kwargs['username'] = self.object.username
        return kwargs

    def get_initial(self):
        """Return the data for initial form load."""
        initial = super().get_initial()
        try:
            ssh_keys = ssh_privileged.get_keys(self.object.username)
            initial['ssh_keys'] = ssh_keys.strip()
            initial['language'] = self.object.userprofile.language
        except Exception:
            pass

        return initial

    def get_success_url(self):
        """Return the URL to redirect to in case of successful updation."""
        return reverse('users:edit', kwargs={'slug': self.object.username})

    def form_valid(self, form):
        """Set the user language if necessary."""

        is_user_deleted = form.cleaned_data.get('delete')
        if is_user_deleted:
            self.success_message = gettext_lazy('User %(username)s deleted.')
        response = super().form_valid(form)
        if is_user_deleted:
            return HttpResponseRedirect(reverse_lazy('users:index'))

        # If user is updating their own profile then set the language for
        # current session too.
        if self.object.username == self.request.user.username:
            translation.set_language(self.request, response,
                                     self.request.user.userprofile.language)

        return response


class UserChangePassword(ContextMixin, SuccessMessageMixin, FormView):
    """View to change user password."""

    template_name = 'users_change_password.html'
    form_class = UserChangePasswordForm
    title = gettext_lazy('Change Password')
    success_message = gettext_lazy('Password changed successfully.')

    def dispatch(self, request, *args, **kwargs):
        """Handle a request and return a HTTP response."""
        if self.request.user.get_username() != self.kwargs['slug'] \
                and not is_user_admin(self.request):
            raise PermissionDenied

        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        """Make the user object available to the form."""
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        kwargs['user'] = User.objects.get(username=self.kwargs['slug'])
        return kwargs

    def get_success_url(self):
        """Return the URL to go to on successful sumbission."""
        return reverse('users:edit', kwargs={'slug': self.kwargs['slug']})

    def form_valid(self, form):
        """Save the form if the submission is valid.

        Django user session authentication hashes are based on password to have
        the ability to logout all sessions on password change.  Update the
        session authentications to ensure that the current sessions is not
        logged out.
        """
        form.save()
        update_session_auth_hash(self.request, form.user)
        return super().form_valid(form)


class FirstBootView(django.views.generic.CreateView):
    """Create user account and log the user in."""

    template_name = 'users_firstboot.html'
    form_class = FirstBootForm

    def dispatch(self, request, *args, **kwargs):
        """Check if there is no possibility to create a new admin account."""
        if request.method == 'POST' and 'skip' in request.POST:
            first_boot.mark_step_done('users_firstboot')
            return HttpResponseRedirect(reverse(first_boot.next_step()))

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        """Add admin users to context data."""
        context = super().get_context_data(*args, **kwargs)
        context['admin_users'] = privileged.get_group_users('admin')
        return context

    def get_form_kwargs(self):
        """Make request available to the form (to insert messages)."""
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_success_url(self):
        """Return the next first boot step after valid form submission."""
        return reverse(first_boot.next_step())


def get_fido2_server(domain: str) -> Fido2Server:
    """Return an instance of a Fido2Server."""
    relying_party = webauthn.PublicKeyCredentialRpEntity(
        id=domain, name='FreedomBox')
    return Fido2Server(relying_party)


def require_owner_or_admin(view_func):
    """Decorator to check if the view is called by owner or admin."""

    @functools.wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        """Wrap a view method and check ownership is valid."""
        if (kwargs['username'] != request.user.get_username()
                and not is_user_admin(request)):
            raise PermissionDenied

        return view_func(request, *args, **kwargs)

    return _wrapped_view


@method_decorator(require_owner_or_admin, name='dispatch')
class PasskeysList(ContextMixin, django.views.generic.ListView):
    """View to show a list of current passkeys for the user."""
    model = UserPasskey
    template_name = 'users_passkeys.html'
    title = gettext_lazy('Passkeys')

    def get_queryset(self):
        """Show only list of passkeys for this user."""
        return self.model.objects.filter(
            user__username=self.kwargs['username']).order_by('created_time')


@json_exception
@require_owner_or_admin
@require_POST
def passkey_add_begin(request, username):
    """Verify passkey registration and add passkey to user's account."""
    user = User.objects.get(username=username)

    # Domain
    domain = request.get_host().partition(':')[0]

    # User
    username = user.get_username()
    user_entity = webauthn.PublicKeyCredentialUserEntity(
        id=user.id, name=username, display_name=username)

    # Begin registration
    server = get_fido2_server(domain)
    create_options, state = server.register_begin(
        user_entity,
        user_verification=webauthn.UserVerificationRequirement.REQUIRED,
        resident_key_requirement=webauthn.ResidentKeyRequirement.PREFERRED)

    logger.info('Passkey creation began for user - %s (%s)', username, user.id)

    request.session['fido2_server_state'] = state
    return JsonResponse(dict(create_options))


def _passkey_get_next_name(user):
    """Return a suitable name for the next passkey of the given user."""
    number = 1
    for passkey in user.passkeys.all():
        match = re.match(r'^Key (\d+)$', passkey.name)
        if match:
            number = max(number, int(match[1]) + 1)

    return f'Key {number}'


@json_exception
@require_owner_or_admin
@require_POST
def passkey_add_complete(request, username):
    """Verify passkey registration and add passkey to user's account."""

    def _response(result: bool, error_string: str):
        """Return a JsonResponse object."""
        status = 200
        if not result:
            status = 400
            logger.error('Error completing passkey registration: %s',
                         error_string)

        return JsonResponse({
            'result': result,
            'error_string': error_string
        }, status=status)

    user = User.objects.get(username=username)

    try:
        response = json.loads(request.body)
    except json.decoder.JSONDecodeError as exception:
        return _response(False, str(exception))

    # Domain
    domain = request.get_host().partition(':')[0]

    # State
    state = request.session.get('fido2_server_state')

    # Complete registration
    server = get_fido2_server(domain)
    try:
        authenticator_data = server.register_complete(state, response)
        logger.info('Passkey creation completed for user - %s (%s)',
                    user.get_username(), user.id)
        assert authenticator_data.is_user_present()
        assert authenticator_data.is_user_verified()
        logger.info('Passkey user is present and verified.')
    except Exception as exception:
        return _response(False, str(exception))

    try:
        credential_data = authenticator_data.credential_data
        UserPasskey.objects.create(
            user=user,
            name=_passkey_get_next_name(user),
            domain=domain,
            signature_counter=authenticator_data.counter,
            registration_flags=authenticator_data.flags,
            extensions=authenticator_data.extensions,
            aaguid=uuid.UUID(f'urn:uuid:{credential_data.aaguid}'),
            credential_id=credential_data.credential_id,
            public_key=fido2.cbor.encode(credential_data.public_key),
        )
    except IntegrityError:
        return _response(False,
                         _('Passkey with that identifier already exists.'))

    return _response(True, None)


@method_decorator(require_owner_or_admin, name='dispatch')
class PasskeyEdit(ContextMixin, UpdateView):
    """View to allow editing a passkey's name."""
    model = UserPasskey
    fields = ['name']
    pk_url_kwarg = 'passkey_id'
    title = _('Edit Passkey')

    def get_template_names(self):
        """Return the template name to use."""
        return ['users_passkey_edit.html']

    def get_success_url(self):
        """Return the URL to visit if form edit succeeds."""
        return reverse('users:passkeys', args=[self.kwargs['username']])


@method_decorator(require_owner_or_admin, name='dispatch')
@method_decorator(require_POST, name='dispatch')
class PasskeyDelete(DeleteView):
    """View to delete a passkey."""
    model = UserPasskey
    pk_url_kwarg = 'passkey_id'

    def get_success_url(self):
        """Return the URL to visit if form edit succeeds."""
        return reverse('users:passkeys', args=[self.kwargs['username']])


@json_exception
@require_POST
def passkey_login_begin(request):
    """Begin the process of logging-in with passwords."""
    # Domain
    domain = request.get_host().partition(':')[0]

    # Begin Authentication
    server = get_fido2_server(domain)
    request_options, state = server.authenticate_begin(
        credentials=None,
        user_verification=fido2.webauthn.UserVerificationRequirement.REQUIRED,
        challenge=None)

    logger.info('Passkey login begins')

    request.session['fido2_server_state'] = state
    return JsonResponse(dict(request_options))


@json_exception
@require_POST
def passkey_login_complete(request):
    """Complete the process of logging-in with passwords."""

    def _response(result: bool, error_string: str):
        """Return a JsonResponse object."""
        status = 200
        if not result:
            status = 400
            logger.error('Error completing passkey login: %s', error_string)

        return JsonResponse({
            'result': result,
            'error_string': error_string
        }, status=status)

    try:
        response = json.loads(request.body)
    except json.decoder.JSONDecodeError as exception:
        return _response(False, str(exception))

    # Domain
    domain = request.get_host().partition(':')[0]

    # State
    state = request.session.get('fido2_server_state')

    # Complete Authentication
    server = get_fido2_server(domain)
    try:
        authentication_repsonse = AuthenticationResponse.from_dict(response)

        if hasattr(authentication_repsonse, 'raw_id'):
            # Library python3-fido2 >= 2.0.0
            credential_id = authentication_repsonse.raw_id
        else:
            # Library python3-fido2 < 2.0.0
            credential_id = authentication_repsonse.id

        selected_passkeys = UserPasskey.objects.filter(
            credential_id=credential_id)

        if not len(selected_passkeys):
            return _response(False, _('Passkey used is not known.'))

        selected_passkey = selected_passkeys[0]

        credentials = [
            AttestedCredentialData.create(
                aaguid=selected_passkey.aaguid.bytes,
                credential_id=selected_passkey.credential_id,
                public_key=fido2.cbor.decode(selected_passkey.public_key))
        ]
        credential_data = server.authenticate_complete(
            state=state, credentials=credentials,
            response=authentication_repsonse)
    except Exception as exception:
        return _response(False, str(exception))

    try:
        passkeys = UserPasskey.objects.filter(
            credential_id=credential_data.credential_id,
            public_key=fido2.cbor.encode(credential_data.public_key))
    except Exception as exception:
        return _response(False, str(exception))

    if not len(passkeys):
        return _response(False, _('Passkey used is not known.'))

    assert len(passkeys) == 1  # credential_id is a unique field.

    passkey = passkeys[0]

    # Detect cloned passkeys using signature counter.
    # See: https://www.w3.org/TR/webauthn/#signature-counter
    authenticator_data = authentication_repsonse.response.authenticator_data
    signature_counter = authenticator_data.counter
    if (passkey.signature_counter and signature_counter
            and signature_counter <= passkey.signature_counter):
        # TODO: Notify user of a cloned passkey
        logger.warning(
            'Potentially cloned passkey detected. Passkey ID in DB - %s, '
            'credential ID - %s, signature counters - %s <= %s', passkey.id,
            fido2.utils.websafe_encode(passkey.credential_id),
            signature_counter, passkey.signature_counter)

    passkey.signature_counter = signature_counter
    passkey.save()  # Update the last used time

    # Needed by login(), stored in session, and used for permission checks.
    passkey.user.backend = 'django.contrib.auth.backends.ModelBackend'

    # Perform user login into Django
    auth_login(request, passkey.user)
    response = _response(True, None)
    if request.user.is_authenticated:
        translation.set_language(request, response,
                                 request.user.userprofile.language)

    return response
