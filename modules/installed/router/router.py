from urlparse import urlparse
import os, cherrypy
from gettext import gettext as _
from plugin_mount import PagePlugin, PluginMount, FormPlugin
from modules.auth import require
from forms import Form
from util import *
import cfg

class router(PagePlugin):
    order = 9 # order of running init in PagePlugins
    def __init__(self, *args, **kwargs):
        self.register_page("router")
        self.menu = cfg.main_menu.add_item("Router", "icon-retweet", "/router", 10)
	self.menu.add_item("Wireless", "icon-signal", "/router/wireless", 12)
	self.menu.add_item("Firewall", "icon-fire", "/router/firewall", 18)
	self.menu.add_item("Hotspot and Mesh", "icon-map-marker", "/router/hotspot")
	self.menu.add_item("Info", "icon-list-alt", "/router/info", 100)

    @cherrypy.expose
    def index(self):
        """This isn't an internal redirect, because we need the url to
        reflect that we've moved down into the submenu hierarchy.
        Otherwise, it's hard to know which menu portion to make active
        or expand or contract."""
        raise cherrypy.HTTPRedirect(cfg.server_dir + '/router/setup')

    @cherrypy.expose
    @require()
    def wireless(self):
        return self.fill_template(title="Wireless", main="<p>wireless setup: essid, etc.</p>")

    @cherrypy.expose
    @require()
    def firewall(self):
        return self.fill_template(title="Firewall", main="<p>Iptables twiddling.</p>")

    @cherrypy.expose
    @require()
    def hotspot(self):
        return self.fill_template(title="Hotspot and Mesh", main="<p>connection sharing setup.</p>")



class setup(PagePlugin):
    def __init__(self, *args, **kwargs):
        self.register_page("router.setup")
        self.menu = cfg.html_root.router.menu.add_item("General Setup", "icon-cog", "/router/setup", 10)
        self.menu.add_item("Dynamic DNS", "icon-flag", "/router/setup/ddns", 20)
        self.menu.add_item("MAC Address Clone", "icon-barcode", "/router/setup/mac_address", 30)

    @cherrypy.expose
    @require()
    def index(self):
        parts = self.forms('/router/setup')
        parts['title'] = "General Router Setup"
        parts['sidebar_right']="""<strong>Introduction</strong><p>Your %s is a replacement for your
wireless router.  By default, it should do everything your usual
router does.  With the addition of some extra modules, its abilities
can rival those of high-end routers costing hundreds of dollars.</p>
""" % cfg.box_name + parts['sidebar_right']
        if not cfg.users.expert():
            parts['main'] += """<p>In basic mode, you don't need to do any
            router setup before you can go online.  Just plug your
            %(product)s in to your cable or DSL modem and the router
            will try to get you on the internet using DHCP.</p>

            <p>If that fails, you might need to resort to the expert
            options.  Enable expert mode in the "%(product)s System /
            Configure" menu.</p>""" % {'product':cfg.box_name}
        else:
            parts['main'] += "<p>router name, domain name, router IP, dhcp</p>"
        return self.fill_template(**parts)

    @cherrypy.expose
    @require()
    def ddns(self):
        return self.fill_template(title="Dynamic DNS", main="<p>Masquerade setup</p>")

    @cherrypy.expose
    @require()
    def mac_address(self):
        return self.fill_template(title="MAC Address Cloning", 
                                  main="<p>Your router can pretend to have a different MAC address on any interface.</p>")


class wan(FormPlugin, PagePlugin):
    url = ["/router/setup"]
    order = 10

    js = """
<script type="text/javascript">
    (function($) {
         function hideshow_static() {
             var show_or_hide = ($('#connect_type').val() == 'Static IP')
             $('#static_ip_form').toggle(show_or_hide);
         }
         $(document).ready(function() {
             $('#connect_type').change(hideshow_static);
             hideshow_static();
         });
     })(jQuery);
</script>"""

    def sidebar_right(self, *args, **kwargs):
        side=''
        if cfg.users.expert():
            side += """<strong>WAN Connection Type</strong>
        <h3>DHCP</h3><p>DHCP allows your router to automatically
        connect with the upstream network.  If you are unsure what
        option to choose, stick with DHCP.  It is usually
        correct.

        <h3>Static IP</h3><p>If you want to setup your connection
        manually, you can enter static IP information.  This option is
        for those who know what they're doing.  As such, it is only
        available in expert mode.</p>"""
        return side

    def main(self, wan_ip0=0, wan_ip1=0, wan_ip2=0, wan_ip3=0, 
             subnet0=0, subnet1=0, subnet2=0, subnet3=0, 
             gateway0=0, gateway1=0, gateway2=0, gateway3=0, 
             dns10=0, dns11=0, dns12=0, dns13=0, 
             dns20=0, dns21=0, dns22=0, dns23=0, 
             dns30=0, dns31=0, dns32=0, dns33=0, 
             message=None, **kwargs):
        if not cfg.users.expert():
            return ''

        store = filedict_con(cfg.store_file, 'router')
        defaults = {'connect_type': 'DHCP'}
        for key, value in defaults.items():
            if not key in kwargs:
                try:
                    kwargs[key] = store[key]
                except KeyError:
                    store[key] = kwargs[key] = value

        form = Form(title="WAN Connection", 
                        action=cfg.server_dir + "/router/setup/wan/index", 
                        name="wan_connection_form",
                        message=message)
        form.dropdown('Connection Type', vals=["DHCP", "Static IP"], id="connect_type")
        form.html('<div id="static_ip_form">')
        form.dotted_quad("WAN IP Address", name="wan_ip", quad=[wan_ip0, wan_ip1, wan_ip2, wan_ip3])
        form.dotted_quad("Subnet Mask", name="subnet", quad=[subnet0, subnet1, subnet2, subnet3])
        form.dotted_quad("Gateway", name="gateway", quad=[gateway0, gateway1, gateway2, gateway3])
        form.dotted_quad("Static DNS 1", name="dns1", quad=[dns10, dns11, dns12, dns13])
        form.dotted_quad("Static DNS 2", name="dns2", quad=[dns20, dns21, dns22, dns23])
        form.dotted_quad("Static DNS 3", name="dns3", quad=[dns30, dns31, dns32, dns33])
        form.html('</div>')
        form.submit("Set Wan")
        return form.render()

