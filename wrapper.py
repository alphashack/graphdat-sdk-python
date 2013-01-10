import graphdat
import time

class Wrapper(object):
    def __init__(self, app):
        print("Wrapper.__init__", app)
    	self.wrapped = app
    	self.graphdat = graphdat.Graphdat()

    def __call__(self, environ, start_response):
        print("Wrapper.__call__", environ, start_response)
        time.clock()
        ret = self.wrapped(environ, start_response)
        self.graphdat.store(environ["REQUEST_METHOD"], environ["REQUEST_URI"], environ["SERVER_NAME"], time.clock())
        return ret
        