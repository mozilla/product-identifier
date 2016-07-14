import sys
import logging
import multiprocessing
import json
from operator import itemgetter
from flask_script import Command, Option, Manager
from gunicorn.app.base import Application as GunicornApplication
from gunicorn.config import Config as GunicornConfig

command_logger_set = False
ListCommand = Manager(usage="list http endpoints enabled")


def setup_command_logger(loglevel=None):
    global command_logger_set
    if not command_logger_set:
        loglevel = loglevel or logging.INFO
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(loglevel)

        try:
            from colorlog import ColoredFormatter
            fmt = ColoredFormatter("%(log_color)s%(message)s",
                                   log_colors={
                                       "DEBUG": "cyan",
                                       "INFO": "green",
                                       "WARNING": "yellow",
                                       "ERROR": "red",
                                       "CRITICAL": "bold_red"})
        except ImportError:
            # fall back to non-colored output
            fmt = logging.Formatter("%(message)s")

        handler.setFormatter(fmt)

        logger = logging.getLogger("command")
        logger.addHandler(handler)
        logger.setLevel(loglevel)
        command_logger_set = True
    else:
        logger = logging.getLogger("command")

    return logger


class GunicornServerCommand(Command):
    """
    Run the Server using gunicorn
    """
    def __init__(self, host='127.0.0.1', port=5000, workers=1,
                 access_logfile='-', max_requests=0, debug=True):
        self.options = {
            "host": host,
            "port": port,
            "workers": workers,
            "access_logfile": access_logfile,
            "max_requests": max_requests,
            "debug": debug,
        }

    def get_options(self):
        options = (
            Option('-H', '--host',
                   dest='host',
                   type=str,
                   default=self.options['host'],
                   help="hostname to bind server to"),
            Option('-p', '--port',
                   dest='port',
                   type=int,
                   default=self.options['port'],
                   help="port to bind server to"),
            Option('-w', '--workers',
                   dest='workers',
                   type=int,
                   default=self.options['workers'],
                   help="set the number of workers"),
            Option('--access-logfile',
                   dest='access_logfile',
                   type=str,
                   default=self.options['access_logfile'],
                   help="set the access log output location"),
            Option('--max-requests',
                   dest='max_requests',
                   type=int,
                   default=self.options['max_requests'],
                   help="set the maximum number of requests " +
                        "to serve before reloading"),
            Option('--no-debug',
                   dest='debug',
                   action='store_false',
                   default=self.options['debug'],
                   help="turn off debug mode"),
        )
        return options

    def run(self, **kwargs):
        self.options.update(kwargs)
        if not kwargs.get('debug'):
            self.options['workers'] = multiprocessing.cpu_count() * 2 + 1

        options = self.options

        class GunicornServer(GunicornApplication):
            def init(self, **kwargs):
                config = {
                    'bind': '{0}:{1}'.format(
                        options['host'],
                        options['port']
                    ),
                    'workers': options['workers'],
                    'worker_class': 'gevent',
                    'accesslog': options['access_logfile'],
                    'max_requests': options['max_requests'],
                }
                return config

            def load(self):
                # Step needed to get around flask's import time side-effects
                from product_identifier.master import Master
                env = Master.instance()
                env.start()
                return env.flask

            def load_config(self):
                # Overriding to prevent Gunicorn from reading
                # the command-line arguments
                self.cfg = GunicornConfig(self.usage, prog=self.prog)
                cfg = self.init()
                if cfg and cfg is not None:
                    for k, v in cfg.items():
                        self.cfg.set(k.lower(), v)

        GunicornServer().run()


@ListCommand.command
def urls():
    """
    Return available endpoints
    """
    logger = setup_command_logger()

    endpoints = []
    from flask import current_app
    for rule in current_app.url_map.iter_rules():
        try:
            endpoints.append((
                rule.rule,
                sorted(list(rule.methods)),
            ))
        except Exception, e:
            logger.error(e)

    endpoints = sorted(endpoints, key=itemgetter(0))
    for url, methods in endpoints:
        logger.info("{0} {1}".format(
            url,
            json.dumps(methods),
        ))
