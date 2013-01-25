#from __future__ import print_function
import wrapper
from time import sleep

@wrapper.Wrapper
def application(env, start_response):
    print("app", env, start_response)
    sleep(0.5)
    start_response('200 OK', [('Content-Type','text/html')])
    return "Hello World"

#ret = app(None, lambda *args: None)
#print("returned", ret)