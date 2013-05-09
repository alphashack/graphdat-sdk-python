import time
from dotdict import dotdict


class Timer(object):
    def __init__(self, name, offset, path, parent):
        # name of the timer ex. bar
        self.name = name
        # time since the request started this was first called
        self.offset = offset
        self.path = path
        self.parent = parent
        self.children = []
        # how many times this timer was called
        self.callcount = 0
        # how many cpu ticks were spent in the request
        self.cputime = 0.0
        # when was the timer was started
        self.lastTimerStart = None
        # total time spent in this timer
        self.responseTime = 0

    def msgpack(self):
        result = dotdict()
        result.firsttimestampoffset = self.offset * 1000
        result.responsetime = self.responseTime
        result.callcount = self.callcount
        result.cputime = self.cputime
        result.name = self.path
        return result

    def __cmp__(self, other):
        return self.name == other.name

    def __eq__(self, other):
        return self.name == other.name

    def __ne__(self, other):
        return self.name != other.name


class Timers(object):

    MAXIMUM_DEPTH = 50
    ROOT_REQUEST = "/"
    REQUEST_KEYS = ("wsgi.url_scheme", "HTTP_HOST", "PATH_INFO", "QUERY_STRING", "REQUEST_METHOD")

    def __init__(self, request, logger):
        self._logger = logger
        self._request = request
        self._requestStart = time.time()

        self._current = None
        self._root = None
        self._routes = {}
        self._routeCount = 0

        self.begin(self.ROOT_REQUEST)
        self._root = self._current

    # def __del__(self):
    #     # end of request
    #     self._endRequest()

    def begin(self, name):
        if not name:
            self._logger.debug("Timer can not be started, name is missing")
            return

        self._beginTimer(name)

    def end(self, name):
        if not name:
            self._logger.debug("Timer can not be ended, name is missing")
            return

        self._endTimer(name)

    def metrics(self):
        # end the open timers
        self._endRequest()

        # msg pack the metrics to only get the data we care about
        context = self._msgpack()

        payload = dotdict()
        payload.type = 'Sample'
        payload.source = 'HTTP'
        payload.route = self._getRequestMethod() + ' ' + self._getRequestPath()
        payload.timestamp = self._requestStart
        payload.cputime = 0.0
        payload.host = self._getRequestHost()
        payload.context = self._msgpack()
        payload.responsetime = context[0].responsetime

        self._logger.debug('Request %s took %f' % (payload.route, payload.responsetime))
        return [payload]

    def _beginTimer(self, name):

        separator = (self._current and self._current.path[-1] != '/') and '/' or ''
        path = (self._current) and self._current.path + separator + name or name
        self._logger.debug("Starting timer for path %s" % path)

        timer = None
        if path in self._routes:
            timer = self._routes[path]
        else:
            offset = time.time() - self._requestStart
            timer = Timer(name, offset, path, self._current)
            self._routes[path] = timer
            if (self._current):
                self._current.children.append(timer)

        timer.callcount += 1
        timer.lastTimerStart = time.time()
        self._current = timer

    def _endTimer(self, name):
        # TODO, walk up the tree to look for any relevant open timers
        if len(self._routes) == 0:
            self._logger.debug('timers :: trying to end timer %s when there are no timers' % name)
            return False
        if self._current is None:
            self._logger.debug('timers :: trying to end timer %s when current is none' % name)
            return False
        if self._current.name != name:
            self._logger.debug('timers :: could not end timer %s because it is not the last timer to begin' % name)
            return False

        duration = (time.time() - self._current.lastTimerStart) * 1000
        self._current.responseTime += duration
        if (self._current.path != self._root.path):
            self._root.responseTime += self._current.responseTime

        self._logger.debug("Ending timer for path %s" % self._current.path)
        self._current = self._current.parent
        return True

    def _endRequest(self):
        # close the requests to get us back to the root
        while self._current is not None:
            if not self._endTimer(self._current.name):
                self._current = None

    def _msgpack(self):
        root = self._routes[self.ROOT_REQUEST]
        metrics = []

        def _msgpack(node):
            metrics.append(node.msgpack())
            for child in node.children:
                _msgpack(child)

        _msgpack(root)
        return metrics

    def _getRequestMethod(self):
        return self._request['REQUEST_METHOD']

    def _getRequestHost(self):
        return self._request['HTTP_HOST'].split(':')[0]

    def _getRequestPath(self):
        path = self._request["PATH_INFO"]
        query_sep = self._request["QUERY_STRING"] and '?' or ''
        query = self._request["QUERY_STRING"]
        return '%s%s%s' % (path, query_sep, query)

    def _getRequestUri(self):
        scheme = self._request["wsgi.url_scheme"]
        host = self._request["HTTP_HOST"]
        path = self._request["PATH_INFO"]
        query_sep = self._request["QUERY_STRING"] and '?' or ''
        query = self._request["QUERY_STRING"]
        uri = '%s://%s%s%s%s' % (scheme, host, path, query_sep, query)
        return uri

    def _isValidRequest(self, request):
        if all(key in self._REQUEST_KEYS for key in request):
            return True
        else:
            return False
