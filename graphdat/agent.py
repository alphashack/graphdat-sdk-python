#!/usr/bin/python

from ctypes import *
sdk = cdll.LoadLibrary("libgraphdat-1.0.so")

sdk.graphdat_init2.argtypes = [c_char_p, c_char_p, c_void_p, c_void_p]
sdk.graphdat_term2.argtypes = [c_void_p]
sdk.graphdat_store2.argtypes = [c_char_p, c_char_p, c_char_p, c_double, c_void_p]

#logger_delegate2_t
LOGFUNC = CFUNCTYPE(None, c_int, c_void_p, c_char_p)

# TODO: better logging
def py_log_func(type, user, msg):
	print("graphdat-sdk-python", type, user, msg)

log_func = LOGFUNC(py_log_func)

class Api(object):
	def __init__(self):
		sdk.graphdat_init2("/tmp/gd.agent.sock", "python", log_func, None)

	def __del__(self):
		self.term()

	def term(self):
		sdk.graphdat_term(None)

	def store(self, method, uri, host, msec):
		sdk.graphdat_store2(method, uri, host, msec, None)
