# -*- coding: utf-8 -*-
import os
import sys
import re
import queue
import socket
import threading
import warnings
import subprocess
CLEANUP_CALLS = queue.Queue()
# _*_ coding:UTF-8 _*_
import time
from threading import Thread, Event

class SafeSocket(object):
    """safe and exact recv & send"""
    def __init__(self, sock=None):
        if sock is None:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        else:
            self.sock = sock
        self.buf = ""

    # PEP 3113 -- Removal of Tuple Parameter Unpacking
    # https://www.python.org/dev/peps/pep-3113/
    def connect(self, tuple_hp):
        host, self.port = tuple_hp
        self.sock.connect((host, self.port))

    def send(self, msg):
        totalsent = 0
        while totalsent < len(msg):
            sent = self.sock.send(msg[totalsent:])
            if sent == 0:
                raise socket.error("socket connection broken")
            totalsent += sent

    def recv(self, size):
        while len(self.buf) < size:
            trunk = self.sock.recv(min(size-len(self.buf), 4096))
            if trunk == "":
                raise socket.error("socket connection broken")
            self.buf += trunk
        ret, self.buf = self.buf[:size], self.buf[size:]
        return ret

    def recv_with_timeout(self, size, timeout=2):
        self.sock.settimeout(timeout)
        try:
            ret = self.recv(size)
        except socket.timeout:
            ret = None
        finally:
            self.sock.settimeout(None)
        return ret

    def recv_nonblocking(self, size):
        self.sock.settimeout(0)
        try:
            ret = self.recv(size)
        except(socket.error) as e:
            #10035 no data when nonblocking
            if e.args[0] == 10035: #errno.EWOULDBLOCK: 尼玛errno似乎不一致
                ret = None
            #10053 connection abort by client
            #10054 connection reset by peer
            elif e.args[0] in [10053, 10054]: #errno.ECONNABORTED:
                raise
            else:
                raise
        return ret

    def close(self):
        self.sock.close()


class NonBlockingStreamReader:

    def __init__(self, stream, raise_EOF=False, print_output=True, print_new_line=True, name=None):
        '''
        stream: the stream to read from.
                Usually a process' stdout or stderr.
        raise_EOF: if True, raise an UnexpectedEndOfStream
                when stream is EOF before kill
        print_output: if True, print when readline
        '''
        self._s = stream
        self._q = queue.Queue()
        self._lastline = None
        self.name = name or id(self)

        def _populateQueue(stream, queue, kill_event):
            '''
            Collect lines from 'stream' and put them in 'quque'.
            '''
            while not kill_event.is_set():
                line = stream.readline()
                if line:
                    queue.put(line)
                    if print_output:
                        # print only new line
                        if print_new_line and line == self._lastline:
                            continue
                        self._lastline = line
                        print  ("[%s]%s" % (self.name, repr(line.strip())))
                elif kill_event.is_set():
                    break
                elif raise_EOF:
                    raise UnexpectedEndOfStream
                else:
                    print("EndOfStream: %s" % self.name)
                    break

        self._kill_event = Event()
        self._t = Thread(target=_populateQueue, args=(self._s, self._q, self._kill_event), name="nbsp_%s"%self.name)
        self._t.daemon = True
        self._t.start()  # start collecting lines from the stream

    def readline(self, timeout=None):
        try:
            return self._q.get(block=timeout is not None, timeout=timeout)
        except queue.Empty:
            return None

    def read(self, timeout=0):
        time.sleep(timeout)
        lines = []
        while True:
            line = self.readline()
            if line is None:
                break
            lines.append(line)
        return b"".join(lines)

    def kill(self):
        self._kill_event.set()


class UnexpectedEndOfStream(Exception):
    pass



class Minitouch(object):
    """
    Super fast operation from minitouch

    References:
    https://github.com/openstf/minitouch
    """

    def __init__(self,port):
        self.server_proc = None
        self.client = None
        self.display_info = None
        self.max_x, self.max_y = None, None
        self.port = port


    def install_and_setup(self,serial,width,height):
        self.serial = serial
        self.WIDTH = width
        self.HEIGHT = height
        #self.setup_server()
        self.setup_client_backend()

    def raw_cmd(self, *args):
        try:
            cmds = ['adb'] + ['-s'] + [self.serial] + list(args)
            p = subprocess.Popen(cmds, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            c = p.communicate()[0]
            return c
        except Exception, e:
            pass

    def __transform_xy(self, x, y):
        """
        Transform coordinates (x, y) according to the device display

        Args:
            x: coordinate x
            y: coordinate y

        Returns:
            transformed coordinates (x, y)

        """
        if not (self.display_info and self.display_info['max_x'] and self.display_info['max_y']):
            return x, y

        width, height = self.wx_x,self.wx_y
        if width > height and self.display_info['orientation'] in [1, 3]:
            width, height = height, width

        nx = x * self.max_x / width
        ny = y * self.max_y / height
        return nx, ny

    def get_std_encoding(self,stream):
        """
        Get encoding of the stream

        Args:
            stream: stream

        Returns:
            encoding or file system encoding

        """
        return getattr(stream, "encoding", None) or sys.getfilesystemencoding()

    def setup_server(self):
        if self.server_proc:
            self.server_proc.kill()
            self.server_proc = None
        cmd = ('adb -s '+ self.serial +' forward tcp:'+ self.port+' localabstract:minitouch')
        out = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        cmds = ('adb -s '+self.serial +" shell /data/local/tmp/minitouch -n " + self.port+" 2>&1")
        p = subprocess.Popen(cmds, stdin=subprocess.PIPE,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        nbsp = NonBlockingStreamReader(p.stdout, name="minitouch_server")
        while True:
            line = nbsp.readline(timeout=5.0)
            if line is None:
                raise RuntimeError("minitouch setup timeout")
            line = line.decode(self.get_std_encoding(sys.stdout))
            # 识别出setup成功的log，并匹配出max_x, max_y
            m = re.match("Type \w touch device .+ \((\d+)x(\d+) with \d+ contacts\) detected on .+ \(.+\)", line)
            if m:
                self.max_x, self.max_y = int(m.group(1)), int(m.group(2))
                break
            else:
                self.max_x = 32768
                self.max_y = 32768
        # nbsp.kill() # 保留，不杀了，后面还会继续读取并pirnt
        if p.poll() is not None:
            # server setup error, may be already setup by others
            # subprocess exit immediately
            raise RuntimeError("minitouch server quit immediately")
        self.server_proc = p
        # reg_cleanup(self.server_proc.kill)
        return p


    def touch(self, tuple_xy, duration=0.01):
        x, y = tuple_xy
        self.handle("d 0 %d %d 50\nc\n" % (x, y))
        time.sleep(duration)
        #self.handle("u 0 \nc\n")

    def touch_end(self):
        self.handle("u 0 \nc\n")

    def move_start(self,tuple_to_xy):
        tox, toy = tuple_to_xy
        self.handle(b"m 0 %d %d 50\nc\n" % (tox, toy))

    def swipe(self, tuple_from_xy, tuple_to_xy, duration=0.8, steps=5):
        """
        Perform swipe event

        minitouch protocol example::

            d 0 0 0 50
            c
            m 0 20 0 50
            c
            m 0 40 0 50
            c
            m 0 60 0 50
            c
            m 0 80 0 50
            c
            m 0 100 0 50
            c
            u 0
            c

        Args:
            tuple_from_xy: start point
            tuple_to_xy: end point
            duration: time interval for swipe duration, default is 0.8
            steps: size of swipe step, default is 5

        Returns:
            None

        """
        from_x, from_y = tuple_from_xy
        to_x, to_y = tuple_to_xy

        from_x, from_y = self.__transform_xy(from_x, from_y)
        to_x, to_y = self.__transform_xy(to_x, to_y)

        interval = float(duration) / (steps + 1)
        self.handle(b"d 0 %d %d 50\nc\n" % (from_x, from_y))
        time.sleep(interval)
        for i in range(1, steps):
            self.handle(b"m 0 %d %d 50\nc\n" % (
                from_x + (to_x - from_x) * i / steps,
                from_y + (to_y - from_y) * i / steps,
            ))
            time.sleep(interval)
        for i in range(10):
            self.handle(b"m 0 %d %d 50\nc\n" % (to_x, to_y))
        time.sleep(interval)
        self.handle(b"u 0\nc\n")


    def pinch(self, center=None, percent=0.5, duration=0.5, steps=5, in_or_out='in'):
        """
        Perform pinch action

        minitouch protocol example::

            d 0 0 100 50
            d 1 100 0 50
            c
            m 0 10 90 50
            m 1 90 10 50
            c
            m 0 20 80 50
            m 1 80 20 50
            c
            m 0 20 80 50
            m 1 80 20 50
            c
            m 0 30 70 50
            m 1 70 30 50
            c
            m 0 40 60 50
            m 1 60 40 50
            c
            m 0 50 50 50
            m 1 50 50 50
            c
            u 0
            u 1
            c
        """
        w, h = self.display_info['width'], self.display_info['height']
        if isinstance(center, (list, tuple)):
            x0, y0 = center
        elif center is None:
            x0, y0 = w / 2, h / 2
        else:
            raise RuntimeError("center should be None or list/tuple, not %s" % repr(center))

        x1, y1 = x0 - w * percent / 2, y0 - h * percent / 2
        x2, y2 = x0 + w * percent / 2, y0 + h * percent / 2
        cmds = []
        if in_or_out == 'in':
            cmds.append(b"d 0 %d %d 50\nd 1 %d %d 50\nc\n" % (x1, y1, x2, y2))
            for i in range(1, steps):
                cmds.append(b"m 0 %d %d 50\nm 1 %d %d 50\nc\n" % (
                    x1+(x0-x1)*i/steps, y1+(y0-y1)*i/steps,
                    x2+(x0-x2)*i/steps, y2+(y0-y2)*i/steps
                ))
            cmds.append(b"m 0 %d %d 50\nm 1 %d %d 50\nc\n" % (x0, y0, x0, y0))
            cmds.append(b"u 0\nu 1\nc\n")
        elif in_or_out == 'out':
            cmds.append(b"d 0 %d %d 50\nd 1 %d %d 50\nc\n" % (x0, y0, x0, y0))
            for i in range(1, steps):
                cmds.append(b"m 0 %d %d 50\nm 1 %d %d 50\nc\n" % (
                    x0+(x1-x0)*i/steps, y0+(y1-y0)*i/steps,
                    x0+(x2-x0)*i/steps, y0+(y2-y0)*i/steps
                ))
            cmds.append(b"m 0 %d %d 50\nm 1 %d %d 50\nc\n" % (x1, y1, x2, y2))
            cmds.append(b"u 0\nu 1\nc\n")
        else:
            raise RuntimeError("center should be 'in' or 'out', not %s" % repr(in_or_out))

        interval = float(duration)/(steps+1)
        for i, c in enumerate(cmds):
            self.handle(c)
            time.sleep(interval)


    def operate(self, args):
        if args["type"] == "down":
            x, y = args["x"], args["y"]
            # support py 3
            cmd = "d 0 %d %d 50 \nc\n" % (x, y)
        elif args["type"] == "move":
            x, y = args["x"], args["y"]
            # support py 3
            cmd = "m 0 %d %d 50 \nc\n" % (x, y)
        elif args["type"] == "up":
            # support py 3
            cmd = "u 0 \nc\n"
        elif args["type"] == "up1":
            # support py 3
            cmd = "u 1 \nc\n"
        else:
            raise RuntimeError("invalid operate args: %s" % args)
        self.handle(cmd)

    def safe_send(self, data):
        """
        Send data to client

        Args:
            data: data to send

        Raises:
            Exception: when data cannot be sent

        Returns:
            None

        """
        try:
            self.client.send(data)
        except Exception as err:
            # raise MinitouchError(err)
            # raise err
           print "send some commands error!"

    def _backend_worker(self):
        """
        Backend worker queue thread

        Returns:
            None

        """
        while not self.backend_stop_event.isSet():
            cmd = self.backend_queue.get()
            if cmd is None:
                break
            self.safe_send(cmd)

    def minitouch_thread(self,serial):
        try:
            cmd = ('adb -s '+serial + ' forward tcp:'+ self.port+' localabstract:minitouch')
            out = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            cmds = ("adb -s "+serial + " shell /data/local/tmp/minitouch")
            p = subprocess.Popen(cmds, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            time.sleep(2)
            self.minitch_flag = True
        except Exception,e:
            import traceback
            traceback.print_exc()
            self.minitch_flag = False

    def setup_client_backend(self):
        self.backend_queue = queue.Queue()
        self.backend_stop_event = threading.Event()
        self.setup_client()
        t = threading.Thread(target=self._backend_worker, name="minitouch")
        t.daemon = True
        t.start()
        self.backend_thread = t
        self.handle = self.backend_queue.put

    def setup_client1(self):
        s = socket.socket()  # 创建 socket 对象
        host = '127.0.0.1'  # 获取本地主机名
        s.connect((host, self.port))
        s.settimeout(2)
        header = ""
        while True:
            try:
                header += s.recv(1024)
                # print header # size is not strict, so use raw socket.recv
            except socket.timeout:
                # raise RuntimeError("minitouch setup client error")
                # warnings.warn("minitouch header not recved")
                break
            if header.count('\n') >= 3:
                break
                #print ("minitouch header:%s", repr(header))
        self.client = s
        self.handle = self.safe_send


    def setup_client(self):
        s = SafeSocket()
        s.connect(('127.0.0.1',int(self.port)))
        s.sock.settimeout(4)
        header = ""
        for i in xrange(0,21):
        #while True:
            try:
                header += s.sock.recv(1024)
                #print header
                #print header # size is not strict, so use raw socket.recv
            except socket.timeout:
                #raise RuntimeError("minitouch setup client error")
                #warnings.warn("minitouch header not recved")
                break
            if header.count('\n') >= 3:
                break
            if i >=20:
                break
            time.sleep(0.2)
        #print ("minitouch header:%s", repr(header))
        self.client = s
        self.handle = self.safe_send

    def teardown(self):
        if hasattr(self, "backend_stop_event"):
            self.backend_stop_event.set()
            self.backend_queue.put(None)
        if self.client:
            self.client.close()
        if self.server_proc:
           self.server_proc.kill()

    def reg_cleanup(self,func, *args, **kwargs):
        """
        Clean the register for given function

        Args:
            func: function name
            *args: optional argument
            **kwargs: optional arguments

        Returns:
            None

        """
        CLEANUP_CALLS.put((func, args, kwargs))
        # atexit.register(func, *args, **kwargs)

    def _cleanup(self):
        # cleanup together to prevent atexit thread issue
        while not CLEANUP_CALLS.empty():
            (func, args, kwargs) = CLEANUP_CALLS.get()
            func(*args, **kwargs)
    def tb(self):
        self.teardown()
        #for i in xrange(0,10):
        self.minitouch_thread("0123456789ABCDEF")
        self.install_and_setup("0123456789ABCDEF",480,960)
        time.sleep(2)
        self.touch((200, 500))
        time.sleep(1)
        self.teardown()
        self.minitouch_thread("0123456789ABCDEF")
        self.install_and_setup("0123456789ABCDEF", 480, 960)
        time.sleep(2)
        self.touch((200, 500))

            #self.install_and_setup("A6DETCTOMRTSV8SG", 480, 960)
if __name__ == "__main__":
    test = Minitouch()
    test.tb()

    #test.swipe((100, 100), (200, 200))