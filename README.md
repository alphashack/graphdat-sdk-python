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
