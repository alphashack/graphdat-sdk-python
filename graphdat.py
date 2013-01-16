#!/usr/bin/python

import agent
import time

class Wrapper(object):
    def __init__(self, app):
    	self.wrapped = app
    	self.api = agent.Api()

    def __call__(self, environ, start_response):
        start_time = time.time()
        ret = self.wrapped(environ, start_response)
        self.api.store(environ["REQUEST_METHOD"], environ["REQUEST_URI"], environ["SERVER_NAME"], (time.time() - start_time) * 1000)
        return ret
