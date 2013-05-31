import functools
import logging
import re
import sys

from agent import Agent
from dotdictionary import DotDictionary
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

    Adding in a list of route regexs in the options willl allow graphdat to
    tokenize urls making the resulting data more generic
    """

    def __init__(self, app, options=None):

        self.graphdat = Graphdat(options)
        self.log = self.graphdat.log

        # compile the regex's if we have any
        self.routes = []
        if options is not None and 'routes' in options:
            for regex in options['routes']:
                if not hasattr(regex, 'match'):
                    self.routes.append(re.compile(regex))
                else:
                    self.routes.append(regex)

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
        #if not 'graphdat' in self.environ:
        #    self.start(self.environ)

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

    HOST = 'localhost'
    PORT = 26873
    SOCKET_FILE = '/tmp/gd.agent.sock'
    VERSION = '2.1'

    def __init__(self, options):

        # make options into an easy to use dictionary
        options = DotDictionary(options or {})

        # should we enable the graphdat SDK to track requests
        if 'enabled' in options:
            self.enabled = bool(options.enabled)
        else:
            self.enabled = True

        # should graphdat log debugging output
        if 'debug' in options:
            self.debug = bool(options.debug)
        else:
            self.debug = False

        # should graphdat dump the messages being sent to the agent
        if 'messageDump' in options:
            self.messageDump = bool(options.messageDump)
        else:
            self.messageDump = False

        # should graphdat use a preconfigured logger
        self._log = DotDictionary()
        if options.logger:
            self._log.error = options.logger.error
            self._log.info = options.logger.info
        else:
            logging.basicConfig(level='INFO')
            self._log.error = logging.error
            self._log.info = logging.info

        # UDP for Windows and File Socket for Linux
        if sys.platform == 'win32':
            self.socketHost = self.HOST  # host is always localhost
            self.socketPort = options.port or self.PORT
        else:
            self.socketFile = options.socketFile or self.SOCKET_FILE

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

    def log(self, msg, *args, **kwargs):
        if self.debug:
            self._log.info(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        if self.debug:
            self._log.error(msg)

    def dump(self, msg, *args, **kwargs):
        if self.messageDump:
            self._log.info(msg, *args, **kwargs)
