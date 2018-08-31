# -*- coding: utf-8 -*-
import os
import Queue
import re
import socket
import struct
import subprocess
import threading
import time
import traceback

class MinitouchStreamMixin(object):
    __touch_queue = None
    __minitouch_process = None

    def __init__(self):
        self.serial = None

    def __install_minitouch(self):
        # install minicap & minitouch
        #os.system('python -m atx minicap')
        pass

    def raw_cmd(self, *args, **kwargs):
        cmds = ['adb','-s',self.serial] + list(args)
        return subprocess.Popen(cmds, **kwargs)

    def open_minitouch_stream(self,  serial = None,port=1111):
        self.serial  = serial
        if self.__touch_queue is None:
            self.__touch_queue = Queue.Queue()

        # ensure minicap installed
        out = self.raw_cmd('shell', 'ls', '"/data/local/tmp/minitouch"', stdout=subprocess.PIPE).communicate()[0]
        if 'No such file or directory' in out:
            self.__install_minitouch()

        if self.__minitouch_process is not None:
            self.__minitouch_process.kill()

        out = self.raw_cmd('shell', 'ps', '-C', '/data/local/tmp/minitouch', stdout=subprocess.PIPE).communicate()[0]
        out = out.strip().split('\n')
        if len(out) > 1:
            p = None
        else:
            p = self.raw_cmd('shell', '/data/local/tmp/minitouch')
            time.sleep(1)
            if p.poll() is not None:
                print 'start minitouch failed.'
                return
        self.__minitouch_process = p                
        self.raw_cmd('forward', 'tcp:%s' % port, 'localabstract:minitouch').wait()

        def send():
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.connect(('127.0.0.1', port))
                while True:
                    cmd = self.__touch_queue.get() # wait here
                    if not cmd:
                        continue
                    elif cmd[-1] != '\n':
                        cmd += '\n'
                    s.send(cmd)    
            except:
                import traceback
                traceback.print_exc()
            finally:
                s.close()
                self.raw_cmd('forward', '--remove', 'tcp:%s' % port).wait()

        t = threading.Thread(target=send)
        t.setDaemon(True)
        t.start()

    def click(self, x, y):
        cmd = 'd 0 %d %d 30\nc\nu 0\nc\n' % (int(x), int(y))
        self.__touch_queue.put(cmd)

    def swipe(self, sx, sy, ex, ey, steps=20):
        x1, y1, x2, y2 = map(int, (x1, y1, x2, y2))
        dx = (x2-x1)/steps
        dy = (y2-y1)/steps
        send = self.touchqueue.put
        send('d 0 %d %d 30\nc\n' % (x1, y1))
        for i in range(steps-1):
            x, y = x1+(i+1)*dx, y1+(i+1)*dy
            send('m 0 %d %d 30\nc\n' % (x, y))
        send('u 0 %d %d 30\nc\nu 0\nc\n' % (x2, y2))

    def pinchin(self, x1, y1, x2, y2, steps=10):
        pass

    def pinchout(self, x1, y1, x2, y2, steps=10):
        pass