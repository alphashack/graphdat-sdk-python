# Graphdat SDK for Python

## A heart rate monitor for you apps

Graphdat lets you visualise the performance of your servers and applications in real time and shows you what to fix.

See an issue, drill into it. Find out the process or line of code causing the bottleneck. Fix it. Deploy code.

Watch in real time the performance improvement.

![preview](http://media.tumblr.com/c350f6338c4955f29f7245fa1e75d309/tumblr_inline_mhctexmC8F1qz4rgp.png)

### Dependencies
* Python 2.6 or greater
* A [Graphdat](http://www.graphdat.com/) account

### Installing

We recommend installing graphdat with pip:

```
pip install graphdat
```
but we support easy_install as well

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

If not (if it is a function from a different module, or created using a factory for example) you can use this method:

```python
application = framework.WSGIHandler() # your existing endpoint
from graphdat import WSGIWrapper
application = WSGIWrapper(application)
```

Graphdat will now graph all of the URLs of your application.

To add another level of integration, you can instrument your code with Graphdat to see deeper level code integration.

### One level deeper


### uWSGI

The only proviso with uWSGI is that is be started with threads enabled. E.g. (this command will start MoinMoin under uWSGI with threads enabled)

```
uwsgi --enable-threads --http :8080 --wsgi-file wiki/server/moin.wsgi
```

### Links

* `Graphdat reference <http://www.graphdat.com/python>`
* `Bug tracker <https://github.com/alphashack/graphdat-sdk-python/issues>`
* `Browse source code <https://github.com/alphashack/graphdat-sdk-python>`
* `Detailed changelog <https://github.com/alphashack/graphdat-sdk-python/commits/master>`


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
