import os
import socket
import struct
import sys
import time
import threading
from Queue import Queue
from msgpack import packb as packs, unpackb as unpacks

__all__ = ['Agent']

# The queue that will hold all of the messages to be sent to graphdat
_queue = Queue()

# The background worker that will push the data to graphdat
_backgroud = None

class Agent(object):
    """
    Validate and package the metrics for graphdat
    """

    def __init__(self, graphdat):

         # the graphdat instance, logger and configuration is stored in here
        if not graphdat:
            raise TypeError
        self._graphdat = graphdat

        if not hasattr(graphdat, 'logger'):
            import logging
            self._logger = logging.getLogger(__name__)
        else:
            self._logger = self._graphdat.logger

        # pid of the process we are running, automatically added to the metrics
        try:
            self._pid = os.getpid()
        except:
            self._pid = 0

        # hostname of the server, automatically added to the metrics
        try:
            self._servername = socket.gethostname()
        except:
            self._severname = "Unknown"

        # create the background worker thread if it is not running already
        if not _backgroud or not _backgroud.isAlive():
            _background = _SendToGraphdatThread(self._graphdat, _queue)
            _background.setDaemon(True)
            _background.start()

    def add(self, metrics):
        """
        Add metrics to your graphdat dashboard
        """

        # if we have no data, no worries, continue on
        if not metrics:
            return

        # if its a string, we cant do anything with it and we shouldnt
        # be getting it in the first place.
        if isinstance(metrics, basestring):
            raise TypeError

        # if its a single metric, just wrap it
        if not hasattr(metrics, "__iter__"):
            metrics = (metrics)

        for sample in metrics:
            # Only HTTP metrics are supported
            if sample.source != 'HTTP':
                continue
            if not sample.route:
                self._logger.debug(
                    "graphdat could not get a the route from the trace")
                continue

            # set the pid the hostname in all metrics
            sample.host = self._servername
            sample.pid = self._pid

            # msgpack the metrics and send  it to the queue
            sample = packs(sample)
            _queue.put(sample)


class _SendToGraphdatThread(threading.Thread):
    """
    Create a separate thread to pull from the queue
    and send the messages to graphdat.
    """

    # How ofter should we process the queue in seconds
    SLEEP_INTERVAL = 2

    def __init__(self, graphdat, queue,
                      sleepInterval=SLEEP_INTERVAL):

        threading.Thread.__init__(self)

        # the graphdat instance and logger
        if not graphdat:
            raise TypeError
        self.graphdat = graphdat

        if not hasattr(graphdat, 'logger'):
            raise TypeError
        self.logger = graphdat.logger
        # the queue to pull the messages from
        if not queue:
            raise TypeError
        self.queue = queue

        # the interval we should sleep if there are no message in the queue
        self.sleepInterval = sleepInterval

        # keep track of the last time we sent the data or a heartbeart
        self.lastSentData = None

        # how we talk to the graphdat agent
        if bool(self.graphdat.socketFile):
            self.transport = _FileSocket(self.graphdat)
        else:
            self.transport = _UDPSocket(self.graphdat)

    def run(self):
        while True:
            # if there are no messages, sleep
            if self.queue.empty():
                time.sleep(self.sleepInterval)

                # if we have been sleeping for a while, the transport
                # layer may need to be notified that we are still alive
                if hasattr(self.transport, 'heartbeatInterval') and self.lastSentData:
                    now = time.time()
                    if (now - self.lastSentData) > self.transport.heartbeatInterval:
                        self.transport.sendHeartbeart()
                        self.lastSentData = now

                # all done here
                continue

            # grab the next message
            message = self.queue.get()

            # send the message
            success = self.transport.send(message)

            # tell the queue we are done
            self.queue.task_done()

            if (success):
                self.logger.debug("Message sent")
                self.logger.debug(unpacks(message, use_list=True))
            else:
                self.logger.error("Sending metrics to Graphdat failed")

class _FileSocket(object):

    """
    Use a File socket to talk to the Graphdat Agent
    """

    # the interval we should send heart beats to the file socket
    HEARTBEAT_INTERVAL = 30
    # How many attempts do we use to send to the file socket.
    SEND_ATTEMPTS = 2

    def __init__(self, graphdat,
                      heartbeatInterval = HEARTBEAT_INTERVAL,
                      sendAttempts = SEND_ATTEMPTS):

        self.logger = graphdat.logger
        self.socketFile = graphdat.socketFile

        # the file socket needs a heart beat to stay open
        self.heartbeatInterval = heartbeatInterval

        # How many attempts do we use to send to the file socket.
        self.sendAttempts = sendAttempts

        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.settimeout(1)
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
                self.sock.sendall(header)

                # if sending the header worked, send the metrics
                if (message):
                    self.sock.sendall(message)

                # success!
                sent = True

            except socket.error:
                self._disconnect()
            except:
                self.logger.error("Unexpected error:", sys.exc_info()[0])

        return sent

    def sendHeartbeart(self):
        """
        Send a heart beat to the socket to let the agent know we are alive
        """
        # just send an empty message
        self.send("")

    def _connect(self):
        try:
            self.logger.info("opening socket %s" % self.socketFile)
            self.sock.connect(self.socketFile)
            self.isOpen = True
        except socket.error, msg:
            self.isOpen = False
            self.logger.error(msg)

    def _disconnect(self):
        if self.sock and hasattr(self.sock, 'close'):
            try:
                self.logger.info("closing socket %s" % self.socketFile)
                self.sock.close()
            except Exception as e:
                self.logger.error(e)
            finally:
                self._socketopen = False

class _UDPSocket(object):
    """
    Use a UDP socket to talk to the Graphdat Agent
    """

    def __init__(self, graphdat):
        self.logger = graphdat.logger
        self.host = graphdat.socketHost
        self.port = graphdat.socketPort
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

         # the UDP socket does not need a heart beat to stay open
        self.heartBeatRequired = False

    def send(self, message):
        """
        Send the metrics to graphdat
        """
        try:
            self.sock.sendto(message, (self.host, self.port))
            return True
        except:
            self.logger.error("Unexpected error:", sys.exc_info()[0])
            return False
