#!/usr/bin/env python
import os

from distutils.core import setup

# List source files in graphdat/lib
exclude_dirs = ['.git']
exclude_files = ['.gitignore']
package_files = []
for root, dirs, files in os.walk('graphdat/lib'):
	files[:] = [f for f in files if f not in exclude_files]
	dirs[:] = [d for d in dirs if d not in exclude_dirs]
	package_files += ['%s/%s' % (root[9:], file) for file in files]

setup(
	name='graphdat',
	version='1.1',
	description='Graphdat instrumentation module',
	long_description='Instrument WSGI applications to send performance data back to your graphs at graphdat.com',
	author='Alphashack',
	author_email='support@graphdat.com',
	url='http://www.graphdat.com',
	packages=['graphdat'],
	package_data={'graphdat': package_files},
)
