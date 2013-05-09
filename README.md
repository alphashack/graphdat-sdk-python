# Graphdat SDK for Python

Graphdat lets you visualise the performance of your servers and applications in real time and shows you what to fix.

For Free. For ever.

It takes 5 minutes to setup after which you can watch your server / app performance in real time on interfaces customised for TV, PC and large / small touch devices. See an issue, drill into it. Find out the process or line of code causing the bottleneck. Fix it. Deploy code. Watch in real time the performance improvement.

![preview](http://media.tumblr.com/c350f6338c4955f29f7245fa1e75d309/tumblr_inline_mhctexmC8F1qz4rgp.png)

### Dependencies
* Python 2.6 or greater
* automake
* build-essential
* libtool
* python-dev
* A [Graphdat](http://www.graphdat.com/) account

Most current Linux distributions (including Mac OS X) comes with Python in the base packages, in order to compile and use the Graphdat python package and its shared library though, you will need some additional tools / libraries.

### Installing

We recommend installing graphdat with pip:

```
pip install graphdat
```

### How to integrate Graphdat with your application

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

### uWSGI

The only proviso with uWSGI is that is be started with threads enabled. E.g. (this command will start MoinMoin under uWSGI with threads enabled)

```
uwsgi --enable-threads --http :8080 --wsgi-file wiki/server/moin.wsgi
```

### Notes

You can either install the graphdat python package, or you can indicate where it is located:

```
PYTHONPATH=~/src/graphdat-sdk-python
```

You can either install the shared library (libgraphdat, this will happen automatically if you install the pythonpackage) or just indicate where it is located:

```
LD_LIBRARY_PATH=/usr/local/lib/
```

We have noticed that on some linux distributions the directory where the library is installed by default is NOT on the default LD_LIBRARY_PATH. In this case you will need to add the path (either temporarily or permanently).

###Contributing

I just created this project for learning some Python. Please help me to make it better!

## Copyright and license

Copyright 2012 Alphashack

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this work except in compliance with the License.
You may obtain a copy of the License in the LICENSE file, or at:

  [http://www.apache.org/licenses/LICENSE-2.0](http://www.apache.org/licenses/LICENSE-2.0)

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
