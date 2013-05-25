import socket
import struct
import sys
import time
import threading
from Queue import Queue
from msgpack import (
    packb as packs,
    unpackb as unpacks
)

__all__ = ['Agent']


class Agent(object):

    """
    Validate and package the metrics for graphdat
    """

    # if the queue gets larger than this, stop adding metrics instead of blocking
    MAX_QUEUE_SIZE = 100

    # The queue will hold all of the messages to be sent to graphdat
    _queue = Queue()

    # The background worker push the data to graphdat
    _backgroundWorker = None

    def __init__(self, graphdat):

        if graphdat is None:
            raise TypeError(
                "the graphdat parameter should not be None")
        self.graphdat = graphdat
        self.log = self.graphdat.log

        # create the background worker thread if it is not running already
        if not self._backgroundWorker or not self._backgroundWorker.isAlive():
            self._backgroundWorker = _SendToGraphdat(self.graphdat, self._queue)
            self._backgroundWorker.setDaemon(True)
            self._backgroundWorker.start()

    def add(self, metrics):
        """
        Add metrics to your graphdat dashboard
        """

        # if we have no data, no worries, continue on
        if metrics is None:
            return

        # if its a string, we cant do anything with it and we shouldnt
        # be getting it in the first place, something is probably wrong
        if isinstance(metrics, str):
            raise TypeError(
                "the metrics should not be a string value")

        # if its a single metric, just wrap it
        if not hasattr(metrics, "__iter__"):
            metrics = (metrics)

        for metric in metrics:
            # Only HTTP metrics are supported
            if metric.source != 'HTTP':
                continue
            if not metric.route:
                self.log("graphdat could not get a the route from the trace")
                continue

            # send the metric to the queue as long as we have room
            if self._queue.qsize() < self.MAX_QUEUE_SIZE:
                self._queue.put(metric)

class _SendToGraphdat(threading.Thread):

    """
    Create a separate thread to pull from the queue
    and send the messages to graphdat.
    """

    def __init__(self, graphdat, queue):

        threading.Thread.__init__(self)

        # the graphdat instance and logger
        if graphdat is None:
            raise TypeError(
                "the graphdat parameter should not be None")
        self.graphdat = graphdat

        self.dump = graphdat.dump
        self.error = graphdat.error
        self.log = graphdat.log

        # the queue to pull the messages from
        if queue is None:
            raise TypeError(
                "the queue parameter should not be None")
        self.queue = queue

        # keep track of the last time we sent the data or a heartbeart
        self.lastSentData = time.time()

        # how we talk to the graphdat agent
        if bool(self.graphdat.socketFile):
            self.transport = _FileSocket(self.graphdat)
        else:
            self.transport = _UDPSocket(self.graphdat)

        # if the transport requires a heartbeat, start it
        if hasattr(self.transport, 'heartbeatInterval'):
            self.__heartbeat()

    def run(self):
        while True:
            # grab the next message
            message = self.queue.get(block=True)

            # we have a message to send, the heart beat
            # can take a break
            self.lastSentData = time.time()

            # msgpack it
            message = packs(message)

            # send the message
            success = self.transport.send(message)

            # tell the queue we are done
            self.queue.task_done()

            if (success):
                self.log("Message sent")
                self.dump(unpacks(message, use_list=True))
            else:
                self.error("Sending metrics to Graphdat failed")

    def __heartbeat(self):
        now = time.time()
        elapsed = now - self.lastSentData

        if elapsed > self.transport.heartbeatInterval:
            self.transport.sendHeartbeart()
            self.lastSentData = now

        # restart the timer
        t = threading.Timer(self.transport.heartbeatInterval, self.__heartbeat)
        t.daemon = True
        t.start()

class _FileSocket(object):

    """
    Use a File socket to talk to the Graphdat Agent
    """

    # the interval we should send heart beats to the file socket
    HEARTBEAT_INTERVAL = 30
    # How many attempts do we use to send to the file socket.
    SEND_ATTEMPTS = 3

    def __init__(self, graphdat,
                      heartbeatInterval = HEARTBEAT_INTERVAL,
                      sendAttempts = SEND_ATTEMPTS):

        self.error = graphdat.error
        self.log = graphdat.log

        # the location of the file socket
        self.socketFile = graphdat.socketFile

        # the file socket needs a hearbeat to stay open
        self.heartbeatInterval = heartbeatInterval

        # How many attempts do we use to send to the file socket.
        self.sendAttempts = sendAttempts

        # the file socket
        self.sock = None
        self.isOpen = False

    def __del__(self):
        self._disconnect()

    def send(self, message):
        """
        Send the metrics to graphdat
        """
        sent = False
        length = len(message)
        header = struct.pack(">i", length)

        for i in range(self.sendAttempts):

            # open the socket if we are not connected
            if not self.isOpen:
                self._connect()

            # if we are still not open, close the socket and try again
            if not self.isOpen:
                self._disconnect()
                continue

            try:
                # we send the header first, it tells the agent how long
                # the message we are sending is
                headerSent = self.sock.send(header)

                # was the header received, if not raise the error and try again
                if headerSent != len(header):
                    raise IOError("Socket connection was broken when sending message header")

                # empty messages are used as a heartbeat to keep the socket connection open
                # we only need to send the header
                if length == 0:
                    sent = True
                    break

                # send the message
                totalSent = 0
                while totalSent < length:
                    sent = self.sock.send(message[totalSent:])
                    if sent == 0:
                        raise IOError("Socket connection was broken while sending message")
                    totalSent += sent

                # success!
                sent = (totalSent == length)
                break

            except IOError, msg:
                self.error("socket error")
                self.error(msg)
                self._disconnect()
            except Exception, msg:
                self.error("Unexpected error")
                self.error(msg)
                self._disconnect()

        return sent

    def sendHeartbeart(self):
        """
        Send a heart beat to the socket to let the agent know we are alive
        """
        # just send an empty message
        self.send("")

    def _connect(self):
        try:
            self.log("opening socket " + self.socketFile)
            self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.sock.settimeout(3)

            self.sock.connect(self.socketFile)
            self.isOpen = True
        except Exception, msg:
            self.error(msg)
            self.isOpen = False

    def _disconnect(self):
        try:
            self.log("closing socket %s" % self.socketFile)
            self.sock.close()
            self.sock = None
        except Exception, msg:
            self.error(msg)

        self.isOpen = False

class _UDPSocket(object):
    """
    Use a UDP socket to talk to the Graphdat Agent
    """

    def __init__(self, graphdat):

        self.error = graphdat.error
        self.host = graphdat.socketHost
        self.port = graphdat.socketPort
        self.sock = None

    def send(self, message):
        """
        Send the metrics to graphdat
        """
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.sendto(message, (self.host, self.port))
            return True
        except:
            self.error("Unexpected error:", sys.exc_info()[0])
            return False
