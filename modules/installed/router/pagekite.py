#
# This file is part of Plinth.
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
Plinth module for configuring PageKite service
"""

import cherrypy
from django import forms
from django.core import validators
from gettext import gettext as _

import actions
import cfg
from modules.auth import require
from plugin_mount import PagePlugin
import util


class PageKite(PagePlugin):
    """PageKite menu entry and introduction page"""
    order = 60

    def __init__(self, *args, **kwargs):
        PagePlugin.__init__(self, *args, **kwargs)

        self.register_page("router.setup.pagekite")
        cfg.html_root.router.setup.menu.add_item(
            _("Public Visibility (PageKite)"), "icon-flag",
            "/router/setup/pagekite", 50)

    @staticmethod
    @cherrypy.expose
    @require()
    def index(**kwargs):
        """Serve introdution page"""
        del kwargs  # Unused

        menu = {'title': _('PageKite'),
                'items': [{'url': '/router/setup/pagekite/configure',
                           'text': _('Configure PageKite')}]}
        sidebar_right = util.render_template(template='menu_block', menu=menu)

        return util.render_template(template='pagekite_introduction',
                                    title=_("Public Visibility (PageKite)"),
                                    sidebar_right=sidebar_right)


class TrimmedCharField(forms.CharField):
    """Trim the contents of a CharField"""
    def clean(self, value):
        """Clean and validate the field value"""
        if value:
            value = value.strip()

        return super(TrimmedCharField, self).clean(value)


class ConfigureForm(forms.Form):  # pylint: disable-msg=W0232
    """Form to configure PageKite"""
    enabled = forms.BooleanField(label=_('Enable PageKite'),
                                 required=False)

    server = forms.CharField(
        label=_('Server'), required=False,
        help_text=_('Currently only pagekite.net server is supported'),
        widget=forms.TextInput(attrs={'placeholder': 'pagekite.net',
                                      'disabled': 'disabled'}))

    kite_name = TrimmedCharField(
        label=_('Kite name'),
        help_text=_('Example: mybox1-myacc.pagekite.me'),
        validators=[
            validators.RegexValidator(r'^[\w-]{1,63}(\.[\w-]{1,63})*$',
                                      _('Invalid kite name'))])

    kite_secret = TrimmedCharField(
        label=_('Kite secret'),
        help_text=_('A secret associated with the kite or the default secret \
for your account if no secret is set on the kite'))

    http_enabled = forms.BooleanField(
        label=_('Web Server (HTTP)'), required=False,
        help_text=_('Site will be available at \
<a href="http://mybox1-myacc.pagekite.me">http://mybox1-myacc.pagekite.me \
</a>'))

    ssh_enabled = forms.BooleanField(
        label=_('Secure Shell (SSH)'), required=False,
        help_text=_('See SSH client setup <a href="\
https://pagekite.net/wiki/Howto/SshOverPageKite/">instructions</a>'))


class Configure(PagePlugin):  # pylint: disable-msg=C0103
    """Main configuration form"""
    order = 65

    def __init__(self, *args, **kwargs):
        PagePlugin.__init__(self, *args, **kwargs)

        self.register_page("router.setup.pagekite.configure")

    @cherrypy.expose
    @require()
    def index(self, **kwargs):
        """Serve the configuration form"""
        status = self.get_status()

        form = None
        messages = []

        if kwargs:
            form = ConfigureForm(kwargs, prefix='pagekite')
            # pylint: disable-msg=E1101
            if form.is_valid():
                self._apply_changes(status, form.cleaned_data, messages)
                status = self.get_status()
                form = ConfigureForm(initial=status, prefix='pagekite')
        else:
            form = ConfigureForm(initial=status, prefix='pagekite')

        return util.render_template(template='pagekite_configure',
                                    title=_('Configure PageKite'), form=form,
                                    messages=messages)

    def get_status(self):
        """
        Return the current status of PageKite configuration by
        executing various actions.
        """
        status = {}

        # Check if PageKite is installed
        output = self._run(['get-installed'])
        cfg.log('Output - %s' % output)
        if output.split()[0] != 'installed':
            return None

        # PageKite service enabled/disabled
        output = self._run(['get-status'])
        status['enabled'] = (output.split()[0] == 'enabled')

        # PageKite kite details
        output = self._run(['get-kite'])
        kite_details = output.split()
        status['kite_name'] = kite_details[0]
        status['kite_secret'] = kite_details[1]

        # Service status
        status['service'] = {}
        for service in ('http', 'ssh'):
            output = self._run(['get-service-status', service])
            status[service + '_enabled'] = (output.split()[0] == 'enabled')

        return status

    def _apply_changes(self, old_status, new_status, messages):
        """Apply the changes to PageKite configuration"""
        cfg.log.info('New status is - %s' % new_status)

        if old_status != new_status:
            self._run(['stop'])

        if old_status['enabled'] != new_status['enabled']:
            if new_status['enabled']:
                self._run(['set-status', 'enable'])
                messages.append(('success', _('PageKite enabled')))
            else:
                self._run(['set-status', 'disable'])
                messages.append(('success', _('PageKite disabled')))

        if old_status['kite_name'] != new_status['kite_name'] or \
                old_status['kite_secret'] != new_status['kite_secret']:
            self._run(['set-kite', '--kite-name', new_status['kite_name'],
                       '--kite-secret', new_status['kite_secret']])
            messages.append(('success', _('Kite details set')))

        for service in ['http', 'ssh']:
            if old_status[service + '_enabled'] != \
                    new_status[service + '_enabled']:
                if new_status[service + '_enabled']:
                    self._run(['set-service-status', service, 'enable'])
                    messages.append(('success', _('Service enabled: {service}')
                                     .format(service=service)))
                else:
                    self._run(['set-service-status', service, 'disable'])
                    messages.append(('success',
                                     _('Service disabled: {service}')
                                     .format(service=service)))

        if old_status != new_status:
            self._run(['start'])

    @staticmethod
    def _run(arguments, superuser=True):
        """Run an given command and raise exception if there was an error"""
        command = 'pagekite-configure'

        cfg.log.info('Running command - %s, %s, %s' % (command, arguments,
                                                       superuser))

        if superuser:
            output, error = actions.superuser_run(command, arguments)
        else:
            output, error = actions.run(command, arguments)

        if error:
            raise Exception('Error setting/getting PageKite confguration - %s'
                            % error)

        return output
