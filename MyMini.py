# -*- coding: utf-8 -*-
import Queue
import Tkinter
import re
import socket
import struct
import subprocess
import threading
import time
import requests
import json
import cv2
import numpy as np
from PIL import Image, ImageTk
import cStringIO
import urllib2
class MyMini():
    def __init__(self, *args, **kwargs):
        self.serial = kwargs.get("serial")
        self.root = kwargs.get("tk")
        self.cav = kwargs.get("cav")
        self.image = None
        self.image_copy = None
        self.img = None
        self.tkimage = None
        self.canvas_image = None
        self.killMinicap()
        self.screen = None
        __minicap_process = None
        self.port = kwargs.get("port")
        self.open_minicap_stream(serial=self.serial)
        self.flag = True

    def str2img(self, jpgstr, orientation=None):
        # arr = np.fromstring(jpgstr, np.uint8)
        arr = np.frombuffer(jpgstr, np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if orientation == 1:
            return cv2.flip(cv2.transpose(img), 0)  # counter-clockwise
        if orientation == 3:
            return cv2.flip(cv2.transpose(img), 1)  # clockwise
        return img

    def raw_cmd(self, *args, **kwargs):
        cmds = ['adb'] + ['-s'] + [self.serial] + list(args)
        return subprocess.Popen(cmds, **kwargs)

    def open_minicap_stream(self, serial=""):
        # if minicap is already started, kill it first.
        self.serial = serial

        out = self.raw_cmd('wait-for-device', 'shell', 'ps', '|grep', 'minicap', stdout=subprocess.PIPE).communicate()[
            0]
        out = out.strip().split('\n')
        if len(out[0]) > 11:
            idx = out[0].split()[1]
            # pid = out[1].split()[idx]
            print 'minicap is running, killing', idx
            self.raw_cmd('wait-for-device', 'shell', 'kill', '-9', idx).wait()

        # start minicap
        out = \
            self.raw_cmd('wait-for-device', 'shell', 'LD_LIBRARY_PATH=/data/local/tmp', '/data/local/tmp/minicap', '-i',
                         stdout=subprocess.PIPE).communicate()[0]
        m = re.search('"width": (\d+).*"height": (\d+).*"rotation": (\d+)', out, re.S)
        w, h, r = map(int, m.groups())
        w, h = min(w, h), max(w, h)
        params = '{x}x{y}@{x1}x{y1}/{r}'.format(x=w, y=h, x1=w, y1=h, r=r)
        cmd = 'wait-for-device shell LD_LIBRARY_PATH=/data/local/tmp /data/local/tmp/minicap -P %s' % params + ' -S -Q 80'
        # cmds = ['adb'] + ['-s'] + [self.serial] + cmd
        p = subprocess.Popen(['adb', '-s', [self.serial], [cmd]], stdout=None)
        # p = self.raw_cmd(cmd,stdout = None)
        self.__minicap_process = p
        time.sleep(0.5)
        # forward to tcp port
        print "minicapport:",self.port
        self.raw_cmd('wait-for-device', 'forward', 'tcp:'+str(self.port), 'localabstract:minicap').wait()

        queue = Queue.Queue()

        # pull data from socket
        def _pull():
            # print 'start pull', p.pid, p.poll()
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                assert p.poll() is None
                s.connect(('127.0.0.1', int(self.port)))
                t = s.recv(24)
                #print 'minicap connected', struct.unpack('<2B5I2B', t)
                while True:
                    frame_size = struct.unpack("<I", s.recv(4))[0]
                    trunks = []
                    recvd_size = 0
                    while recvd_size < frame_size:
                        trunk_size = min(8192, frame_size - recvd_size)
                        d = s.recv(trunk_size)
                        trunks.append(d)
                        recvd_size += len(d)
                    queue.put(''.join(trunks))
            except Exception as e:
                if not isinstance(e, struct.error):
                    pass
                    # traceback.print_exc()
                if p.poll() is not None:
                    try:
                        print p.stdout.read()
                    except Exception, e:
                        pass
                else:
                    print 'stoping minicap ...'
                    p.kill()
            finally:
                s.close()
                self.raw_cmd('wait-for-device', 'forward', '--remove', 'tcp:'+str(self.port)).wait()

        t = threading.Thread(target=_pull)
        t.setDaemon(True)
        t.start()

        out = self.raw_cmd('wait-for-device', 'shell', 'getprop', 'ro.build.version.sdk',
                           stdout=subprocess.PIPE).communicate()[0]
        sdk = int(out.strip())
        orientation = r / 90

        def _listen():
            while True:
                try:
                    time.sleep(0.01)
                    frame = queue.get_nowait()
                    if sdk <= 16:
                        img = self.str2img(frame, orientation)
                    else:
                        img = self.str2img(frame)
                    self.screen = img
                except Queue.Empty:
                    if p.poll() is not None:
                        # print 'minicap died'
                        try:
                            p.stdout.read()
                            break
                        except:
                            break
                    continue
                except:
                    # traceback.print_exc()
                    pass

        t = threading.Thread(target=_listen)
        t.setDaemon(True)
        t.start()

    def killMinicap(self):
        self.flag =False
        out = \
            self.raw_cmd('wait-for-device', 'shell', 'ps', '|grep', 'minicap', stdout=subprocess.PIPE).communicate()[
                0]
        out = out.strip().split('\n')
        if len(out[0]) > 11:
            idx = out[0].split()[1]
            # pid = out[1].split()[idx]
            # print 'minicap is running, killing', idx
            self.raw_cmd('wait-for-device', 'shell', 'kill', '-9', idx).wait()
        time.sleep(1)

    def screen_simple(self):
        try:
            if len(self.serial) > 0 and self.flag:
                self.img = self.screen
                while self.img is None:
                    time.sleep(0.5)
                    self.img = self.screen
                if len(self.img)> 10:
                    self.image = Image.fromarray(self.img[:, :, ::-1])
                    self.image_copy = self.image
                    self.image = self.image.resize((360, 720), Image.ANTIALIAS)
                    self.tkimage = ImageTk.PhotoImage(self.image)
                    w, h = self.image.size
                    # w = w if w<h else h
                    # h = h if w < h else w
                    self.cav.config(width=w, height=h)
                    if self.canvas_image is None:
                        self.canvas_image = self.cav.create_image(0, 0, anchor=Tkinter.NW, image=self.tkimage)
                    else:
                        self.cav.itemconfig(self.canvas_image, image=self.tkimage)
                    self.root.after(20, self.screen_simple)

        except Exception,e:
            print "mini fail",e.message
            # import traceback
            # traceback.print_exc()
        # finally:
        #     self.root.after(30, self.screen_simple)

    def screen_simple_threading(self):
        threading.Thread(target=self.screen_simple).start()

    def crop_image(self):
        for i in xrange(0,3):
            if self.image_copy.size[0]>0:
                return self.image_copy
            else:
                time.sleep(0.5)
        return None


    def post_image(self):
        img = cv2.imread("facetmp.png")
        res = {"image": str(img.tolist()).encode('base64')}
        _ = requests.post("192.168.33.32:8081", data=json.dumps(res))

    def ImageScale(self):
        self.post_image()
        file = cStringIO.StringIO(urllib2.urlopen("192.168.33.32:8081").read())
        img = Image.open(file)
        img.show()

if __name__ == "__main__":
    ist = MyMini(serial="NVJ74H4L55SW85GI", tk=None, cav=None)

    ist.ImageScale()

