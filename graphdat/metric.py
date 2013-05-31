import os
import time
from dotdictionary import DotDictionary

__all__ = ['Metric']

# pid of the process we are running, automatically added to the metrics
try:
    PID = os.getpid()
except:
    PID = 0

class Metric(object):
    """
    The set of values that are sent to the Graphdat dashboard for
    each request

    Graphdat is expecting metrics the following format:
    {
        "cputime": 49.635,
        "host": "www.graphdat.com",
        "pid": "90904",
        "responsetime": 49.414,
        "route": "GET /",
        "source": "HTTP",
        "timestamp": 1353535694666.753,
        "type": "Sample",
        "context": [{
             "callcount": 1,
             "cputime": 49.635,
             "firsttimestampoffset": 0.09912109375,
             "name": "/"
             "responsetime": 49.414,
        }, {
             "callcount": 1,
             "cputime": 45.623,
             "firsttimestampoffset": 3.8701171875,
             "name": "/render"
             "responsetime": 45.502,
         }]
    }
    """

    # the depth of children a timer is allowed to have
    MAXIMUM_DEPTH = 50
    # the starting point for a timer
    ROOT_REQUEST = "/"
    # keys that need to be in the request for a valid metric
    REQUEST_KEYS = ("HTTP_HOST", "REQUEST_METHOD", "PATH_INFO")

    def __init__(self, request, regexRoutes, infoLogger, errorLogger):
        self.request = request
        self.regexRoutes = regexRoutes
        self.log = infoLogger
        self.error = errorLogger

        # we measure the offsets of the subsequent timers
        # off the request start time
        self.requestStart = time.time()

        # the current timer, so we know where we are in the hierarchy
        self.current = None
        # all of the timers so we can increment individual counts
        self.routes = {}

        # start the first timer
        self.begin(self.ROOT_REQUEST)

    def begin(self, name):
        """
        begin a timer.

        A timer has a unique path, but may reuse the same name
        ex. /foo/foo/bar is valid
        """
        if name is None:
            self.log("Timer can not be started, name is missing")
            return

        self._beginTimer(name)

    def end(self, name):
        """
        end a timer.
        """
        if name is None:
            self.log("Timer can not be ended, name is missing")
            return

        self._endTimer(name)

    def compile(self):
        """
        End the open timers in the hierarchy and create the data for graphdat
        Your dashboard only needs a subset of the data
        """

        # end the open timers in the request
        self._endAllTimers()

        # get only the metrics that we care about for all of the timers
        context = self._compileTimers()

        payload = DotDictionary({
            'context': context,
            'host': self._getRequestHost(),
            'pid': PID,
            'responsetime': context[0].responsetime,
            'route': self._getRequestMethod() + ' ' + self._getRequestPath(),
            'source': 'HTTP',
            'timestamp': self.requestStart,
            'type': 'Sample',
        })

        self.log('Request %s took %f' % (payload.route, payload.responsetime))
        return [payload]

    def _beginTimer(self, name):

        separator = (self.current and self.current.path[-1] != '/') and '/' or ''
        path = (self.current) and self.current.path + separator + name or name

        depth = path.count('/')
        if (depth > self.MAXIMUM_DEPTH):
            # sometimes some code ends up in a recursive loop, lets not create timers for each one of those accidents
            self.error("The timer stack is too deep.  The current hierarchy is %d levels deep, maximum depth is %d", (depth, self.MAXIMUM_DEPTH))
            return

        self.log("Starting timer for path %s" % path)

        # if we have a route for this, get it, otherwise create a new one
        if path in self.routes:
            timer = self.routes[path]
        else:
            offset = time.time() - self.requestStart
            timer = Timer(name, offset, path, self.current)
            self.routes[path] = timer
            if (self.current):
                self.current.children.append(timer)

        # increment the counter and reset the timer in case we have the same
        # path twice, otherwise the numbers will get skewed
        timer.callcount += 1
        timer.lastTimerStart = time.time()
        self.current = timer

    def _endTimer(self, name):

        if len(self.routes) == 0:
            self.log('timers :: trying to end timer %s when there are no timers' % name)
            return False
        if self.current is None:
            self.log('timers :: trying to end timer %s when current is none' % name)
            return False
        if self.current.name != name:
            self.log('timers :: could not end timer %s because it is not the last timer to begin' % name)
            return False

        duration = (time.time() - self.current.lastTimerStart) * 1000  # need it in milliseconds
        self.current.responseTime += duration

        self.log("Ending timer for path %s" % self.current.path)
        self.current = self.current.parent
        return True

    def _endAllTimers(self):
        # close the requests to get us back to the root
        while self.current is not None:
            if not self._endTimer(self.current.name):
                self.current = None

    def _compileTimers(self):
        root = self.routes[self.ROOT_REQUEST]
        metrics = []

        def __compileTimers(node):
            metrics.append(node.compile())
            for child in node.children:
                __compileTimers(child)

        __compileTimers(root)
        return metrics

    def _getRequestMethod(self):
        return self.request['REQUEST_METHOD']

    def _getRequestHost(self):
        return self.request['HTTP_HOST'].split(':')[0]

    def _getRequestPath(self):
        path = self.request["PATH_INFO"]
        query_sep = self.request["QUERY_STRING"] and '?' or ''
        query = self.request["QUERY_STRING"]
        uri = '%s%s%s' % (path, query_sep, query)

        if (self.regexRoutes):
            uri_no_slash = uri.lstrip('/')
            for regex in self.regexRoutes:
                match = regex.match(uri_no_slash)
                if match:
                    return self._replace(regex, uri_no_slash)
        return uri

    def _replace(self, regex, value):
        # check the args
        if (regex is None or not value):
            return value
        # does the regex match
        search = regex.search(value)
        if (not search):
            return value
        groups = search.groups()
        if (len(groups) == 0):
            return value
        # do the replacement
        index = 0
        keys = dict(zip(regex.groupindex.values(), regex.groupindex.keys()))
        newValue = ''
        for i in range(1, len(groups) + 1):
            key = (keys and i in keys) and (':' + keys[i]) or '?'
            newValue += (value[index:search.start(i)] + key)
            index = search.end(i)
        newValue += value[index:]
        return newValue

class Timer(object):
    """
    The deeper level of route Metrics

    Every request has a Metric, but if you instument your application by
    using 'begin' and 'end' blocks, Graphdat can show you where your
    code is spending the most amount of time
    """

    def __init__(self, name, offset, path, parent):
        # name of the timer ex. bar
        self.name = name
        # offset time since the request started this was first called
        self.offset = offset
        # path of the time ex. /foo/bar
        self.path = path
        # the parent and children of the timer so we can traverse
        # up the tree to close timers if needed.
        self.parent = parent
        self.children = []
        # how many times this timer was called
        self.callcount = 0
        # when was the timer was started
        self.lastTimerStart = None
        # total time spent in this timer
        self.responseTime = 0

    def compile(self):
        """
        When we send the metrics off to graphdat, we only care about
        a subset of the information
        """
        result = DotDictionary()
        result.callcount = self.callcount
        result.firsttimestampoffset = self.offset * 1000
        result.name = self.path
        result.responsetime = self.responseTime
        return result
