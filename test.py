import time
from ctypes import *
gd = cdll.LoadLibrary("libgraphdat-1.0.0.so")

gd.graphdat_init2.argtypes = [c_char_p, c_char_p, c_void_p, c_void_p]
gd.graphdat_term2.argtypes = [c_void_p]
gd.graphdat_store2.argtypes = [c_char_p, c_char_p, c_char_p, c_double, c_void_p]

#logger_delegate2_t
LOGFUNC = CFUNCTYPE(None, c_int, c_void_p, c_char_p)

def py_log_func(type, user, msg):
	print("log", type, user, msg)

log_func = LOGFUNC(py_log_func)

gd.graphdat_init2("/tmp/gd.agent.sock", "python", log_func, None)
gd.graphdat_store2("GET", "/", "MAC", 7, None)

time.sleep(1)

gd.graphdat_term(None)
