import functools
import logging
import sys
import time

from agent import Agent
import import_hook
from dotdict import dotdict
from timers import Timers


try:
    import resource
    hasResource = True
except ImportError:
    # only works in some linux environments
    hasResource = False

# Register our importer which implements post import hooks for
# triggering of callbacks to monkey patch modules before import
# returns them to caller.
sys.meta_path.insert(0, import_hook.ImportHookFinder())


class graphdat(object):

    def __init__(self):

        # Graphdat global vars
        self.name = 'Python'
        self.version = '0.2'
        self.enabled = True
        self.ignore_errors = True
        self.options = dotdict()

        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.DEBUG)

        # Graphdat debugging vars
        self.debug = dotdict()
        self.debug.context_begin = True
        self.debug.context_end = True
        self.debug.context_trace = True

        # Graphdat Socket Vars, UDP for Windows and File Socket for Linux
        self.socketFile = (sys.platform == 'win32') and None or '/tmp/gd.agent.sock'
        self.socketHost = 'localhost'
        self.socketPort = 26873
        self.socketDesc = self.socketFile and self.socketFile or (self.socketHost + ':' + self.socketPort)

        # TODO: setup frameworks
        # TODO: setup proxy

        self.logger.info("Graphdat (v%s) is %s" % (self.version, self.enabled and 'enabled' or 'disabled'))

        # Create the agent so we can start collecting metrics
        self.agent = Agent(self)

        if self.debug:
            self.logger.debug('Graphdat is running in debug mode')
        if self.enabled:
            self.logger.info("Will send to agent on %s" % self.socketDesc)

    def config(self, options):
        if options is not None:
            self.options = options
            if options.enabled is not None:
                self.enabled = bool(options.enabled)
            if options.debug is not None:
                self.debug = bool(options.debug)
            if options.logger is not None:
                self.logger = options.logger
            if sys.platform is 'win32' and options.port is not None:
                self.port = options.port
                self._socketDesc = self.socketHost + ':' + self.socketPort
            if sys.platform is not 'win32' and options.socketFile is not None:
                self.socketFile = options.socketFile
                self._socketDesc = self.socketFile

    def cputime(self):
        if hasResource:
            ru_time = 0
            usage = resource.getrusage(resource.RUSAGE_SELF)
            ru_time += hasattr(usage, 'ru_utime') and usage.ru_utime or 0
            ru_time += hasattr(usage, 'ru_stime') and usage.ru_stime or 0
            return ru_time
        else:
            return None

    def log(self, message):
        if self.debug and message:
            self.logger.debug(message)

    def error(self, e):
        self.logger.error(e)

    def dump(self, data):
        if self.debug:
            self.logger.debug(data)


def wsgi_application():
    def decorator(wrapped):
        return WSGIWrapper(wrapped)
    return decorator


def wrap_wsgi_application(application):
    return WSGIWrapper(application)


class WSGIWrapper(object):

    def __init__(self, app):

        self._graphdat = graphdat()
        self._logger = self._graphdat.logger

        functools.update_wrapper(self, app, available_attrs(app))
        self.wrapped = app
        print "wrapped"

    def __get__(self, instance, klass):
        print "__get__"
        print instance
        if instance is None:
            return self

        desc = self.wrapped.__get__(instance, klass)
        return self.__class__(desc)

    def __call__(self, environ, start_response):
        print "__call__"

        # add graphdat to the request so you can call the begin & end methods
        self._onRequestStart(environ)

        try:
            result = self.wrapped(environ, self._start_response(environ, start_response))
        except BaseException, e:
            self._logger.exception(e)
            raise

        #return Iterable(trace, result)
        return result

    def _start_response(self, environ, start_response):
        def callback(status, headers, exc_info=None):
            # save the metrics
            self._onRequestEnd(environ)

            # Call upstream start_response
            start_response(status, headers, exc_info)
        return callback

    def _onRequestStart(self, request):
        timers = Timers(request, self._graphdat.logger)
        request['graphdat'] = timers
        return request

    def _onRequestEnd(self, request):
        if not request or 'graphdat' not in request:
            return

        timers = request['graphdat']
        metrics = timers.metrics()
        if (metrics):
            self._graphdat.agent.add(metrics)


class Iterable(object):
    def __init__(self, trace, generator):
        self.trace = trace
        self.generator = generator

    def __iter__(self):
        if not self.trace._start:
            self.trace._start = time.time()

        for item in self.generator:
            yield item

    def close(self):
        try:
            if hasattr(self.generator, 'close'):
                self.generator.close()
        except:
            self.trace.__exit__(*sys.exc_info())
        else:
            self.trace.__exit__(None, None, None)


def available_attrs(f):
    # http://bugs.python.org/issue3445
    return tuple(a for a in
                 functools.WRAPPER_ASSIGNMENTS
                 if hasattr(f, a))
