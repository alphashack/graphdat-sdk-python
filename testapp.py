#from __future__ import print_function
import wrapper

@wrapper.Wrapper
def application(env, start_response):
    print("app", env, start_response)
    start_response('200 OK', [('Content-Type','text/html')])
    return "Hello World"

#ret = app(None, lambda *args: None)
#print("returned", ret)
