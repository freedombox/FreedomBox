import cherrypy
import cfg
from plugin_mount import PagePlugin
from modules.forms import Form
from auth import *
# Controller to provide login and logout actions

class AuthController(PagePlugin):
    def __init__(self, *args, **kwargs):
        PagePlugin.__init__(self, *args, **kwargs)
        self.register_page("auth")

    def on_login(self, username):
        """Called on successful login"""
    
    def on_logout(self, username):
        """Called on logout"""
    
    def get_loginform(self, username, msg='', from_page=cfg.server_dir+"/"):
        form = Form(title="Login", action=cfg.server_dir + "/auth/login", message=msg)
        form.text_input(name="from_page", value=from_page, type="hidden")
        form.text_input("Username", name="username", value=username)
        form.text_input("Passphrase", name="passphrase", type="password")
        form.submit(label="Login")

        return self.fill_template(main=form.render(), sidebar_right=" ")
    
    @cherrypy.expose
    def login(self, username=None, passphrase=None, from_page=cfg.server_dir+"/", **kwargs):
        if username is None or passphrase is None:
            return self.get_loginform("", from_page=from_page)
        
        error_msg = check_credentials(username, passphrase)
        if error_msg:
            return self.get_loginform(username, error_msg, from_page)
        else:
            cherrypy.session[cfg.session_key] = cherrypy.request.login = username
            self.on_login(username)
            raise cherrypy.HTTPRedirect(from_page or (cfg.server_dir + "/"))
    
    @cherrypy.expose
    def logout(self, from_page=cfg.server_dir+"/"):
        sess = cherrypy.session
        username = sess.get(cfg.session_key, None)
        sess[cfg.session_key] = None
        if username:
            cherrypy.request.login = None
            self.on_logout(username)
        raise cherrypy.HTTPRedirect(from_page or (cfg.server_dir + "/"))
