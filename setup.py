try:
    from setuptools import setup
except:
    from distutils.core import setup

setup(
    name='graphdat',
    version='2.1',
    author='Graphdat',
    author_email='support@graphdat.com',
    packages=['graphdat'],
    url='http:/www.graphdat.com',
    license='Apache License 2.0',
    description='Graphdat instrumentation module',
    long_description=open('README.txt').read(),
    install_requires=[
        "msgpack-python >= 0.3.0",
    ],
)
