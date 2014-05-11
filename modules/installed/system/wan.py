import cherrypy
from django import forms
from gettext import gettext as _
from modules.auth import require
from plugin_mount import PagePlugin
import cfg
import util


class WanForm(forms.Form):  # pylint: disable-msg=W0232
    """Form to configure wan settings"""

    wan_admin = forms.BooleanField(
        label=_('Allow access to Plinth from WAN'),
        required=False,
        help_text=_('If you check this box, this front end will be reachable \
from the WAN.  If your {{ box_name }} connects you to the internet, that \
means you\'ll be able to log in to the front end from the internet.  This \
might be convenient, but it is also <strong>dangerous</strong>, since it can \
enable attackers to gain access to your {{ box_name }} from the outside \
world. All they\'ll need is your username and passphrase, which they might \
guess or they might simply try every posible combination of letters and \
numbers until they get in.  If you enable the WAN administration option, you \
<strong>must</strong> use long and complex passphrases.').format(
            box_name=cfg.box_name))

    lan_ssh = forms.BooleanField(
        label=_('Allow SSH access from LAN'),
        required=False)

    wan_ssh = forms.BooleanField(
        label=_('Allow SSH access from WAN'),
        required=False)

    # XXX: Only present due to issue with submitting empty form
    dummy = forms.CharField(label='Dummy', initial='dummy',
                            widget=forms.HiddenInput())


class Wan(PagePlugin):
    order = 60

    def __init__(self, *args, **kwargs):
        PagePlugin.__init__(self, *args, **kwargs)
        self.register_page('sys.config.wan')

        cfg.html_root.sys.config.menu.add_item(_('WAN'), 'icon-cog',
                                               '/sys/config/wan', 20)

    @cherrypy.expose
    @require()
    def index(self, **kwargs):
        """Serve the configuration form"""
        status = self.get_status()

        form = None
        messages = []

        if kwargs and cfg.users.expert():
            form = WanForm(kwargs, prefix='wan')
            # pylint: disable-msg=E1101
            if form.is_valid():
                self._apply_changes(form.cleaned_data, messages)
                status = self.get_status()
                form = WanForm(initial=status, prefix='wan')
        else:
            form = WanForm(initial=status, prefix='wan')

        title = _('Accessing the {box_name}').format(box_name=cfg.box_name)
        return util.render_template(template='wan', title=title, form=form,
                                    messages=messages)

    @staticmethod
    def get_status():
        """Return the current status"""
        return util.filedict_con(cfg.store_file, 'sys')

    @staticmethod
    def _apply_changes(new_status, messages):
        """Apply the changes after form submission"""
        store = util.filedict_con(cfg.store_file, 'sys')
        for field in ['wan_admin', 'wan_ssh', 'lan_ssh']:
            store[field] = new_status[field]

        messages.append(('success', _('Setting updated')))
