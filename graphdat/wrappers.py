#!/usr/bin/python

import agent
import time

class WSGIWrapper(object):
    def __init__(self, app):
    	self.wrapped = app
    	self.api = agent.Api()

    def __call__(self, environ, start_response):
        start_time = time.time()
        ret = self.wrapped(environ, start_response)
	request_uri = '%(scheme)s://%(host)s%(path)s%(query_sep)s%(query)s' % \
		{'scheme': environ["wsgi.url_scheme"], 'host': environ["HTTP_HOST"], 'path': environ["PATH_INFO"], 'query_sep': '?' if environ["QUERY_STRING"] else '', 'query': environ["QUERY_STRING"]}
        self.api.store(environ["REQUEST_METHOD"], request_uri, environ["SERVER_NAME"], (time.time() - start_time) * 1000)
        return ret
