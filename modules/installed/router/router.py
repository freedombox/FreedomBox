import cherrypy
from django import forms
from gettext import gettext as _
from plugin_mount import PagePlugin
from modules.auth import require
import cfg
import util


class Router(PagePlugin):
    """Router page"""
    order = 9  # order of running init in PagePlugins

    def __init__(self, *args, **kwargs):
        PagePlugin.__init__(self, args, kwargs)

        self.register_page('router')

        self.menu = cfg.main_menu.add_item('Router', 'icon-retweet', '/router',
                                           10)
        self.menu.add_item('Wireless', 'icon-signal', '/router/wireless', 12)
        self.menu.add_item('Firewall', 'icon-fire', '/router/firewall', 18)
        self.menu.add_item('Hotspot and Mesh', 'icon-map-marker',
                           '/router/hotspot')
        self.menu.add_item('Info', 'icon-list-alt', '/router/info', 100)

    @staticmethod
    @cherrypy.expose
    def index():
        """This isn't an internal redirect, because we need the url to
        reflect that we've moved down into the submenu hierarchy.
        Otherwise, it's hard to know which menu portion to make active
        or expand or contract."""
        raise cherrypy.HTTPRedirect(cfg.server_dir + '/router/setup')

    @staticmethod
    @cherrypy.expose
    @require()
    def wireless():
        """Serve the wireless page"""
        return util.render_template(title="Wireless",
                                    main="<p>wireless setup: essid, etc.</p>")

    @staticmethod
    @cherrypy.expose
    @require()
    def firewall():
        """Serve the firewall page"""
        return util.render_template(title="Firewall",
                                    main="<p>Iptables twiddling.</p>")

    @staticmethod
    @cherrypy.expose
    @require()
    def hotspot():
        """Serve the hotspot page"""
        return util.render_template(title="Hotspot and Mesh",
                                    main="<p>connection sharing setup.</p>")


class WANForm(forms.Form):  # pylint: disable-msg=W0232
    """WAN setup form"""
    connection_type = forms.ChoiceField(
        label=_('Connection Type'),
        choices=[('dhcp', _('DHCP')), ('static_ip', _('Static IP'))])

    wan_ip = forms.IPAddressField(label=_('WAN IP Address'), required=False)

    subnet_mask = forms.IPAddressField(label=_('Subnet Mask'), required=False)

    dns_1 = forms.IPAddressField(label=_('Static DNS 1'), required=False)

    dns_2 = forms.IPAddressField(label=_('Static DNS 2'), required=False)

    dns_3 = forms.IPAddressField(label=_('Static DNS 3'), required=False)


class Setup(PagePlugin):
    """Router setup page"""
    def __init__(self, *args, **kwargs):
        PagePlugin.__init__(self, args, kwargs)

        self.register_page('router.setup')

        self.menu = cfg.html_root.router.menu.add_item(
            'General Setup', 'icon-cog', '/router/setup', 10)
        self.menu.add_item('Dynamic DNS', 'icon-flag', '/router/setup/ddns',
                           20)
        self.menu.add_item('MAC Address Clone', 'icon-barcode',
                           '/router/setup/mac_address', 30)

    @cherrypy.expose
    @require()
    def index(self, **kwargs):
        """Return the setup page"""
        status = self.get_status()

        form = None
        messages = []

        if kwargs:
            form = WANForm(kwargs, prefix='router')
            # pylint: disable-msg=E1101
            if form.is_valid():
                self._apply_changes(status, form.cleaned_data, messages)
                status = self.get_status()
                form = WANForm(initial=status, prefix='router')
        else:
            form = WANForm(initial=status, prefix='router')

        return util.render_template(template='router_setup',
                                    title=_('General Router Setup'),
                                    form=form, messages=messages)

    @staticmethod
    @cherrypy.expose
    @require()
    def ddns():
        """Return the DDNS page"""
        return util.render_template(title="Dynamic DNS",
                                    main="<p>Masquerade setup</p>")

    @staticmethod
    @cherrypy.expose
    @require()
    def mac_address():
        """Return the MAC address page"""
        return util.render_template(
            title="MAC Address Cloning",
            main="<p>Your router can pretend to have a different MAC address \
on any interface.</p>")

    @staticmethod
    def get_status():
        """Return the current status"""
        store = util.filedict_con(cfg.store_file, 'router')
        return {'connection_type': store.get('connection_type', 'dhcp')}

    @staticmethod
    def _apply_changes(old_status, new_status, messages):
        """Apply the changes"""
        print 'Apply changes - %s, %s', old_status, new_status
        if old_status['connection_type'] == new_status['connection_type']:
            return

        store = util.filedict_con(cfg.store_file, 'router')
        store['connection_type'] = new_status['connection_type']

        messages.append(('success', _('Connection type set')))
        messages.append(('info', _('IP address settings unimplemented')))
