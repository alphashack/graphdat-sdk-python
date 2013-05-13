import os
import socket
import struct
import sys
import time
from Queue import Queue
#from msgpack_pure import packs, unpacks
from msgpack import packb as packs, unpackb as unpacks

# TODO:
# - put sending of messages into their own thread
# - add in a heartbeat on its own thread
# - make agent a singleton

class Agent(object):

    def __init__(self, graphdat):
        self._graphdat = graphdat
        self._logger = self._graphdat.logger
        self._pid = str(os.getpid())
        self._queue = Queue()
        self._servername = socket.gethostname()

        self._send = None
        self._sock = None
        self._socketopen = False
        self._useFileSocket = bool(self._graphdat.socketFile)

        self._lastSentData = None
        self._opensocket()

    def __del__(self):
        self._closesocket()

    def add(self, metrics):
        if not metrics or len(metrics) == 0:
            return
        for sample in metrics:
            if sample.source != 'HTTP':
                continue
            if not sample.route:
                self._logger.debug("graphdat could not get the route from the trace")
                continue

            sample.pid = self._pid

            sample = packs(sample)

            # HACK - put this into its own thread
            self._queue.put(sample)
            if not self._queue.empty():
                self._send(self._queue.get())

    def _opensocket(self):
        self._logger.info('attempting connection to %s' % self._graphdat.socketDesc)
        try:
            if self._useFileSocket:
                self._send = self._sendfilesocket
                self._sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                self._sock.connect(self._graphdat.socketFile)
                self._socketopen = True
            else:
                self._send = self._sendudp
                self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                self._socketopen = True

            self._send = self._sendlogger
        except socket.error, msg:
            self._socketopen = False
            self._logger.error(msg)

    def _closesocket(self):
        if self._sock and hasattr(self._sock, 'close') and self._useFileSocket:
            try:
                self._logger.info('closing socket %s' % self._graphdat.socketDesc)
                self._sock.close()
            except Exception as e:
                self._logger.error(e)

    def _send(self, message):
        retries = 2
        sent = False

        packed = packs(message)
        length = len(packed)

        buffer = struct.pack('iiii',
                             length >> 24,
                             length >> 16,
                             length >> 8,
                             length)

        for i in range(retries):
            if not self._socketopen:
                self._opensocket()
            if not self._socketopen:
                self._closesocket()
                continue

            try:
                self._send(buffer)
                if (message):
                    self._send(packed)
                    sent = True
                    self._lastSentData = time.time()
            except socket.error:
                self._closesocket()
            except:
                self._logger.error("Unexpected error:", sys.exc_info()[0])

            if (sent):
                self._logger.debug("Message sent: " + unpacks(message))
                break
            else:
                self._logger.error("self._send: Sending message failed")

    def _sendheartbeart(self):
        self._send("")

    def _sendlogger(self, message):
        message = unpacks(message)
        self._logger.info(message)

    def _sendfilesocket(self, message):
        self._sock.sendall(message)

    def _sendudp(self, message):
        self._sock.sendto(message, (self._graphdat.socketHost, self._graphdat.socketPort))
