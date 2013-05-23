import functools
import logging
import re
import sys

from agent import Agent
from metric import Metric

__all__ = ['WSGIWrapper', 'wsgi_application', 'wrap_wsgi_application']

# use a decorator to wrap your wsgi application
def wsgi_application():
    def decorator(wrapped):
        return WSGIWrapper(wrapped)
    return decorator

def wrap_wsgi_application(application):
    return WSGIWrapper(application)

class WSGIWrapper(object):

    """
    The wsgi wrapper used to instrument python apps

    Graphdat automatically tracks the URLs and their durations
    and sends the data to graphdat.  Graphdat is also added to the
    environ to allow custom drill downs.

    Adding in a list of route regexs will allow graphdat to tokenize
    urls making the resulting data more generic
    """

    def __init__(self, app, options=None, routes=None):

        self.graphdat = Graphdat(options)
        self.log = self.graphdat.log

        # compile the regex's if we have any
        if routes is not None:
            for i in range(len(routes)):
                regex = routes[i]
                if not hasattr(regex, 'match'):
                    routes[i] = re.compile(regex)
        self.routes = routes

        # wrap the application
        self.log('wrapping application')
        functools.update_wrapper(self, app, self._available_attrs(app))
        self.wrapped = app

    def __call__(self, environ, start_response):

        # add graphdat to the request so you can call the begin & end methods
        self._onRequestStart(environ)

        try:
            result = self.wrapped(environ, start_response)
        except BaseException, e:
            self.graphdat.error(e)
            self._onRequestEnd(environ)
            raise

        # return an iterable incase we have a generator
        return Iterable(self._onRequestStart, self._onRequestEnd, environ, result)

    def _onRequestStart(self, request):
        metric = Metric(request, self.routes, self.graphdat.log, self.graphdat.error)
        request['graphdat'] = metric
        return request

    def _onRequestEnd(self, request):
        # if graphdat is not part of the request, we cannot
        # get the metric, so we just return
        if request is None or 'graphdat' not in request:
            return

        # compile the metrics of the request and send them to graphdat
        metric = request['graphdat']
        data = metric.compile()
        if data is not None:
            self.graphdat.add(data)

    def _available_attrs(self, f):
    # http://bugs.python.org/issue3445
        return tuple(a for a in
            functools.WRAPPER_ASSIGNMENTS
            if hasattr(f, a))

class Iterable(object):
    def __init__(self, start, end, environ, generator):
        self.start = start
        self.end = end
        self.environ = environ
        self.generator = generator

    def __iter__(self):
        if not 'graphdat' in self.environ:
            self.start(self.environ)

        for item in self.generator:
            yield item

    def close(self):
        try:
            if hasattr(self.generator, 'close'):
                self.generator.close()
        finally:
            self.end(self.environ)

class Graphdat(object):

    """
    Graphat configuration
    """

    NAME = 'Python'
    HOST = 'localhost'
    PORT = 26873
    SOCKET_FILE = '/tmp/gd.agent.sock'
    VERSION = '0.2'

    def __init__(self, options):

        if options is None:
            options = {}

        # should we enable the graphdat SDK to track requests
        if 'enabled' in options:
            self.enabled = bool(options['enabled'])
        else:
            self.enabled = True

        # should graphdat log debugging output
        if 'debug' in options:
            self.debug = bool(options['debug'])
        else:
            self.debug = True

        # should graphdat dump the messages being sent to the agent
        if 'messageDump' in options:
            self.messageDump = bool(options['messageDump'])
        else:
            self.messageDump = True

        # use a preconfigured logger
        if 'logger' in options:
            logger = options['logger']
            self._error = logger.error
            self._info = logger.info
        else:
            logging.basicConfig(level='INFO')
            self._error = logging.error
            self._info = logging.info

        # UDP for Windows and File Socket for Linux
        if sys.platform == 'win32':
            if 'port' in options:
                self.socketPort = options['port']
            else:
                self.socketPort = self.PORT
            # host is always localhost
            self.socketHost = self.HOST
        else:
            if 'socketFile' in options:
                self.socketFile = options['socketFile']
            else:
                self.socketFile = self.SOCKET_FILE

        self.log("Graphdat (v%s) is %s" % (self.VERSION, self.enabled and 'enabled' or 'disabled'))

        # Create the agent so we can start collecting metrics
        self.agent = Agent(self)

        if self.debug:
            self.log('Graphdat is running in debug mode')
        if self.enabled:
            self.log("Will send to agent on %s" % self.target)

    @property
    def target(self):
        if self.socketFile:
            return self.socketFile
        else:
            return self.socketHost + ':' + self.socketPort

    def add(self, metrics):
        self.agent.add(metrics)

    def log(self, message):
        if self.debug and message is not None:
            self._info(message)

    def error(self, message):
        if self.debug and message is not None:
            self._error(message)

    def dump(self, data):
        if self.messageDump and data is not None:
            self._info(data)
