graphdat-sdk-python
===================

Python module for Graphdat. To find out more about graphdat visit http://dashboard.graphdat.com/landing

To use the module, you need to wrap your WSGI application entry point with the supplied graphdat wrapper.
If you have a declared function endpoint then you can use the decorator:

from graphdat_sdk_python import *
@graphdat.Wrapper
def application(environ, start_response { # your existing endpoint
	...
}

If not (say if it is a function from a different module, or created using a factory) you can use this method:

application = make_application() # your existing endpoint
from graphdat_sdk_python import *
application = graphdat.Wrapper((application))

uWSGI
-----

The only proviso with uWSGI is that is be started with threads enabled. E.g. (this is the command to start MoinMoin under uWSGI with threads enabled)

PYTHONPATH=~/src/ uwsgi --enable-threads http :8080 --wsgi-file wiki/server/moin.wsgi
