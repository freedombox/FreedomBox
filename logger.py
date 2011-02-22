import cherrypy
import inspect
import cfg

cherrypy.log.error_file = cfg.status_log_file
cherrypy.log.access_file = cfg.access_log_file
cherrypy.log.screen = False

class Logger():
    """By convention, log levels are DEBUG, INFO, WARNING, ERROR and CRITICAL."""
    def log(self, msg, level="DEBUG"):
        try:
            username = cherrypy.session.get(cfg.session_key)
        except AttributeError:
            username = ''
        cherrypy.log.error("%s %s %s" % (username, level, msg), inspect.stack()[2][3], 20)
    def __call__(self, *args):
        self.log(*args)

    def debug(self, msg):
        self.log(msg)

    def info(self, msg):
        self.log(msg, "INFO")

    def warn(self, msg):
        self.log(msg, "WARNING")

    def warning(self, msg):
        self.log(msg, "WARNING")

    def error(self, msg):
        self.log(msg, "ERROR")

    def err(self, msg):
        self.error(msg)

    def critical(self, msg):
        self.log(msg, "CRITICAL")
