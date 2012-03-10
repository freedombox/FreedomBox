import cherrypy
from modules.auth import require
from plugin_mount import PagePlugin
import cfg

class FileExplorer(PagePlugin):
    def __init__(self, *args, **kwargs):
        PagePlugin.__init__(self, *args, **kwargs)
        self.register_page("sharing.explorer")
        cfg.html_root.sharing.menu.add_item("File Explorer", "icon-folder-open", "/sharing/explorer", 30)

    @cherrypy.expose
    @require()
    def index(self):
        main = """
<p>File explorer for users that also have shell accounts.</p> <p>Until
that is written (and it will be a while), we should install <a
href="http://www.mollify.org/demo.php">mollify</a> or <a
href="http://www.ajaxplorer.info/wordpress/demo/">ajaxplorer</a>, but
of which seem to have some support for playing media files in the
browser (as opposed to forcing users to download and play them
locally).  The downsides to third-party explorers are: they're don't
fit within our theme system, they require separate login, and they're
written in php, which will make integrating them hard.</p>

<p>There are, of course, many other options for php-based file
explorers.  These were the ones I saw that might do built-in media
players.</p>

<p>For python-friendly options, check out <a
href="http://blogfreakz.com/jquery/web-based-filemanager/">FileManager</a>.
It appears to be mostly javascript with some bindings to make it
python-friendly.</p>
"""
        return self.fill_template(title="File Explorer", main=main, sidebar_right='')
