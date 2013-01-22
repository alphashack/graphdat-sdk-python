#!/usr/bin/env python
import os

# File system helper

class cd:
    def __init__(self, path):
        self.path = path

    def __enter__(self):
        self.cwd = os.getcwd()
        os.chdir(self.path)

    def __exit__(self, *args):
        os.chdir(self.cwd)

# Redefine build to configure, make, install shared lib

from distutils.command.build import build
from distutils import log

class Build(build):
	def run(self):
		log.info("Configuring Graphdat Shared Library")
		with cd("graphdat/lib/module_graphdat"):
			os.system("chmod u+x config.guess")
			os.system("chmod u+x config.sub")
			os.system("chmod u+x configure")
			os.system("chmod u+x depcomp")
			os.system("chmod u+x install-sh")
			os.system("chmod u+x ltmain.sh")
			os.system("chmod u+x missing")
			os.system("./configure")
			log.info("Building Graphdat Shared Library")
			os.system("make")
			log.info("Installing Graphdat Shared Library")
			os.system("make install")
		build.run(self)

# List source files in graphdat/lib

exclude_dirs = ['.git']
exclude_files = ['.gitignore']
package_files = []
for root, dirs, files in os.walk('graphdat/lib'):
	files[:] = [f for f in files if f not in exclude_files]
	dirs[:] = [d for d in dirs if d not in exclude_dirs]
	package_files += ['%s/%s' % (root[9:], file) for file in files]

# Run the setup

from distutils.core import setup

setup(
	cmdclass={'build' : Build},
	name='graphdat',
	version='1.2',
	description='Graphdat instrumentation module',
	long_description='Instrument WSGI applications to send performance data back to your graphs at graphdat.com',
	author='Alphashack',
	author_email='support@graphdat.com',
	url='http://www.graphdat.com',
	packages=['graphdat'],
	package_data={'graphdat': package_files},
)
