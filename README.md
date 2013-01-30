graphdat-sdk-python
===================

Python module for Graphdat. To find out more about graphdat visit http://dashboard.graphdat.com/landing

Installation
------------

We recommend installing graphdat with pip:

```
pip install graphdat
```


Integration
-----------

To use the module, you need to wrap your WSGI application entry point with the supplied graphdat wrapper.

If you have a declared function endpoint then you can use the decorator:

```python
from graphdat import WSGIWrapper
@WSGIWrapper
def application(environ, start_response { # your existing endpoint
	...
}
```

If not (say if it is a function from a different module, or created using a factory) you can use this method:

```python
application = framework.WSGIHandler() # your existing endpoint
from graphdat import WSGIWrapper
application = WSGIWrapper(application)
```

uWSGI
-----

The only proviso with uWSGI is that is be started with threads enabled. E.g. (this command will start MoinMoin under uWSGI with threads enabled)

```
uwsgi --enable-threads --http :8080 --wsgi-file wiki/server/moin.wsgi
```

Dependencies
------------

In order to correctly compile and use the python package and its shared library, you will need these tools / libraries:

build-essential
automake
python-dev
libtool


Notes
-----

You can either install the graphdat python package, or you can indicate where it is located:

```
PYTHONPATH=~/src/graphdat-sdk-python
```

You can either install the shared library (libgraphdat, this will happen automatically if you install the pythonpackage) or just indicate where it is located:

```
LD_LIBRARY_PATH=/usr/local/lib/
```

We have noticed that on some linux distributions the directory where the library is installed by default is NOT on the default LD_LIBRARY_PATH. In this case you will need to add the path (either temporarily or permanently).
