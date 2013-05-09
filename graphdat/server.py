#! /usr/bin/env python

# Our tutorial's WSGI server
from wsgiref.simple_server import make_server


def application(environ, start_response):

    environ['graphdat'].begin("mike")
    # Soting and stringifying the environment key, value pairs
    response_body = ['%s: %s' % (key, value) for key, value in sorted(environ.items())]
    response_body = '\n'.join(response_body)

    status = '200 OK'
    response_headers = [('Content-Type', 'text/plain'),
                        ('Content-Length', str(len(response_body)))]
    environ['graphdat'].end("mike")
    start_response(status, response_headers)

    return [response_body]

import graphdat
application = graphdat.WSGIWrapper(application)

# Instantiate the WSGI server.
# It will receive the request, pass it to the application
# and send the application's response to the client
if __name__ == '__main__':
    server = make_server(
        'localhost',  # The host name.
        8051,  # A port number where to wait for the request.
        application  # Our application object name, in this case a function.
    )
    server.serve_forever()

# # iterable
# def send_file(file_path, size):
#     with open(file_path) as f:
#         block = f.read(BLOCK_SIZE)
#         while block:
#             yield block
#             block = f.read(BLOCK_SIZE)

# size = os.path.getsize(file_path)
# headers = [
#     ("Content-type", mimetype),
#     ("Content-length", str(size)),
# ]
# start_response("200 OK", headers)
# return send_file(file_path, size)
