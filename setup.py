#!/usr/bin/env python

from distutils.core import setup

setup(
	name='graphdat',
	version='1.0',
	description='Graphdat instrumentation module',
	long_description='Instrument WSGI applications to send performance data back to your graphs at graphdat.com',
	author='Alphashack',
	author_email='support@graphdat.com',
	url='http://www.graphdat.com',
	packages=['graphdat'],
)
