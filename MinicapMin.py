# -*- coding: utf-8 -*-
import Queue
import Tkinter
import os
import re
import socket
import struct
import subprocess
import threading
import time
import traceback
from datetime import datetime

import cv2
import numpy as np
from PIL import Image, ImageTk


def str2img(jpgstr, orientation=None):
    # arr = np.fromstring(jpgstr, np.uint8)
    arr = np.frombuffer(jpgstr, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if orientation == 1:
        return cv2.flip(cv2.transpose(img), 0)  # counter-clockwise
    if orientation == 3:
        return cv2.flip(cv2.transpose(img), 1)  # clockwise
    return img


class MinicapStreamMixin():
    __screen = None
    __minicap_process = None

    def __init__(self, *args, **kwargs):
        pass

    def __install_minicap(self):
        # install minicap & minitouch
        # os.system('python -m atx minicap')
        cpu = self.raw_cmd( 'shell', 'getprop', 'ro.product.cpu.abi',
                           stdout=subprocess.PIPE).communicate()[0]
        cpu = cpu.strip()
        sdk = self.raw_cmd( 'shell', 'getprop', 'ro.build.version.sdk',
                           stdout=subprocess.PIPE).communicate()[0]
        sdk = sdk.strip()
        self.raw_cmd('push', os.getcwd() + '/lib/' + sdk + '/' + cpu + '/minicap.so','/data/local/tmp/',
                           stdout=subprocess.PIPE).communicate()[0]
        self.raw_cmd('push', os.getcwd() + '/lib/' + sdk + '/' + cpu + '/minicap',
                         '/data/local/tmp/',
                         stdout=subprocess.PIPE).communicate()[0]
        self.raw_cmd('shell', 'chmod', '777', '/data/local/tmp/minicap',
                         stdout=subprocess.PIPE).communicate()[0]
        self.raw_cmd('push', os.getcwd() + '/lib/armeabi-v7a/minitouch', '/data/local/tmp')
        self.raw_cmd('shell', 'chmod', '755', '/data/local/tmp/minitouch')

    def open_minicap_stream(self, port=1313, serial=""):
        # ensure minicap installed
        # out = self.raw_cmd('shell', 'ls', '"/data/local/tmp/minicap"',
        #                    stdout=subprocess.PIPE).communicate()[0]
        # if 'No such file or directory' in out or len(out) < 2:
        #     self.__install_minicap()

        if self.__minicap_process is not None:
            self.__minicap_process.kill()


        # if minicap is already started, kill it first.
        out = self.raw_cmd('shell', 'ps', '|grep', 'minicap', stdout=subprocess.PIPE).communicate()[0]
        out = out.strip().split('\n')
        if len(out[0]) > 11:
            idx = out[0].split()[1]
            # pid = out[1].split()[idx]
            print 'minicap is running, killing', idx
            self.raw_cmd('shell', 'kill', '-9', idx).wait()

        # start minicap
        out = \
            self.raw_cmd('shell', 'LD_LIBRARY_PATH=/data/local/tmp', '/data/local/tmp/minicap', '-i',
                         stdout=subprocess.PIPE).communicate()[0]
        m = re.search('"width": (\d+).*"height": (\d+).*"rotation": (\d+)', out, re.S)
        w, h, r = map(int, m.groups())
        w, h = min(w, h), max(w, h)
        params = '{x}x{y}@{x1}x{y1}/{r}'.format(x=w, y=h, x1=w, y1=h, r=0)
        cmd = 'shell LD_LIBRARY_PATH=/data/local/tmp /data/local/tmp/minicap -P %s' % params + ' -S -Q 80'
        # cmds = ['adb'] + ['-s'] + [self.serial] + cmd
        p = subprocess.Popen(['adb', '-s', [self.serial], [cmd]], stdout=None)
        # p = self.raw_cmd(cmd,stdout = None)
        self.__minicap_process = p
        time.sleep(0.5)
        # forward to tcp port
        self.raw_cmd('forward', 'tcp:%s' % port, 'localabstract:minicap').wait()
        self.raw_cmd('forward','tcp:1111','localabstract:minitouch').wait()
        self.raw_cmd('shell','/data/local/tmp/minitouch').wait()
        queue = Queue.Queue()

        # pull data from socket
        def _pull():
            # print 'start pull', p.pid, p.poll()
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                assert p.poll() is None
                s.connect(('127.0.0.1', port))
                t = s.recv(24)
                print 'minicap connected', struct.unpack('<2B5I2B', t)
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
                self.raw_cmd( 'forward', '--remove', 'tcp:%s' % port).wait()

        t = threading.Thread(target=_pull)
        t.setDaemon(True)
        t.start()

        out = self.raw_cmd( 'shell', 'getprop', 'ro.build.version.sdk',
                           stdout=subprocess.PIPE).communicate()[0]
        sdk = int(out.strip())
        orientation = r / 90

        def _listen():
            while True:
                try:
                    time.sleep(0.01)
                    frame = queue.get_nowait()
                    if sdk <= 16:
                        img = str2img(frame, orientation)
                    else:
                        img = str2img(frame)
                    self.__screen = img
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

    def screenshot_cv2(self):
        return self.__screen


class DummyDevice(object):
    def raw_cmd(self, *args, **kwargs):
        cmds = ['adb'] + ['-s'] + [self.serial] + list(args)
        return subprocess.Popen(cmds, **kwargs)


class TestDevice(MinicapStreamMixin, DummyDevice):
    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)
        self.serial = kwargs.get("serial")
        self.open_minicap_stream()
        self.shootflag = True
        # self.clearRecent()

    def mathc_img(self, sourceimage, targetimage, value=0.9):
        img_rgb = cv2.imread(sourceimage)
        img_gray = cv2.cvtColor(img_rgb, cv2.COLOR_BGR2GRAY)
        template = cv2.imread(targetimage, 0)
        w, h = template.shape[::-1]
        res = cv2.matchTemplate(img_gray, template, cv2.TM_CCOEFF_NORMED)
        threshold = value
        xy = []
        loc = np.where(res >= threshold)
        pts = zip(*loc[::-1])
        # print len(pts)
        for pt in pts:
            cv2.rectangle(img_rgb, pt, (pt[0] + w, pt[1] + h), (7, 249, 151), 2)
            # print pt[0], pt[1], w, h
            xy.append([pt[0] + w / 2, pt[1] + h / 2])
        return xy

    def findpng(self, cp, appname):
        start = "null"
        for li in os.listdir(os.getcwd() + "/pic"):
            xy = self.mathc_img(os.getcwd() + "/pic/" + li, os.getcwd() + "/cpm/" + str(cp), 0.95)
            if len(xy) > 0:
                st = os.path.splitext(li)[0].split("_")
                stm = 0
                if str(st[1]) > 0:
                    start = str(st[0]) + "." + str(st[1])
                # print "<" + appname + ">启动时:", str(start) + "秒,[" + "位置]", xy[0]
                # self.removeFileInFirstDir(os.getcwd() + "/pic")
                # print li
                break
        return start

    def tap(self, xy):
        if "x" in xy:
            x = xy.split("x")[0]
            y = xy.split("x")[1]
        elif "X" in xy:
            x = xy.split("X")[0]
            y = xy.split("Y")[1]
        elif "," in xy:
            x = xy.split(",")[0]
            y = xy.split(",")[1]
        cmd = 'shell input tap ' + x + " " + y + " "
        p = subprocess.Popen(['adb', '-s', [self.serial], [cmd]], stdout=subprocess.PIPE).communicate()[0]
        # out = self.raw_cmd('wait-for-device', 'shell', 'input', 'tap',x,y,stdout=subprocess.PIPE).communicate()[0]

    def getLauncher(self, xy):
        self.removeFileInFirstDir(os.getcwd() + "/pic")
        self.tap(xy)
        stflg = True
        try:
            while self.shootflag:
                img = self.screenshot_cv2()
                if img is not None:
                    if stflg:
                        starttime = datetime.now()
                        stflg = False
                    endtime = datetime.now()
                    dmn = (endtime - starttime).seconds
                    dms = (endtime - starttime).microseconds
                    dms = '%06d' % dms
                    imgpath = os.getcwd() + "/pic/" + str(dmn) + "_" + str(dms) + ".png"
                    cv2.imwrite(imgpath, img)
                    time.sleep(0.01)
                cv2.waitKey(20)
        except Exception, e:
            traceback.print_exc()
            pass

    def removeFileInFirstDir(self, targetDir):
        for file in os.listdir(targetDir):
            targetFile = os.path.join(targetDir, file)
            if os.path.isfile(targetFile):
                os.remove(targetFile)

    def killMinicap(self):
        out = self.raw_cmd('shell', 'ps', '|grep', 'minicap', stdout=subprocess.PIPE).communicate()[
            0]
        out = out.strip().split('\n')
        if len(out[0]) > 11:
            idx = out[0].split()[1]
            # pid = out[1].split()[idx]
            # print 'minicap is running, killing', idx
            self.raw_cmd( 'shell', 'kill', '-9', idx).wait()
        time.sleep(2)

    def testAppStartTime(self, cuttime, xy):
        try:
            #print "time,", cuttime
            t = threading.Thread(target=self.getLauncher, args=(xy,))
            t.setDaemon(True)
            t.start()
            time.sleep(int(cuttime))
            self.shootflag = False
            time.sleep(1)
        except Exception, e:
            print e.message
        finally:
            self.killMinicap()



class screen_with_controls(MinicapStreamMixin, DummyDevice):
    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)
        self.serial = kwargs.get("serial")
        self.root = kwargs.get("tk")
        self.cav = kwargs.get("cav")
        self.image = None
        self.image_copy = None
        self.img = None
        self.tkimage = None
        self.canvas_image = None
        #self.killMinicap()
        self.open_minicap_stream()

    def killMinicap(self):
            out = \
            self.raw_cmd( 'shell', 'ps', '|grep', 'minicap', stdout=subprocess.PIPE).communicate()[
                0]
            out = out.strip().split('\n')
            if len(out[0]) > 11:
                idx = out[0].split()[1]
                # pid = out[1].split()[idx]
                # print 'minicap is running, killing', idx
                self.raw_cmd( 'shell', 'kill', '-9', idx).wait()
            time.sleep(2)

    def screen_simple(self):
        if len(self.serial)>0:
            self.img = self.screenshot_cv2()
            while self.img is None:
                time.sleep(1)
                self.img = self.screenshot_cv2()

            self.image = Image.fromarray(self.img[:, :, ::-1])
            self.image_copy = self.image
            self.image = self.image.resize((360, 720), Image.ANTIALIAS)

            self.tkimage = ImageTk.PhotoImage(self.image)
            w, h = self.image.size
            self.cav.config(width=w, height=h)
            if self.canvas_image is None:
                self.canvas_image = self.cav.create_image(0, 0, anchor=Tkinter.NW, image=self.tkimage)
            else:
                self.cav.itemconfig(self.canvas_image, image=self.tkimage)
            self.root.after(10, self.screen_simple)

    def crop_image(self):
        return self.image_copy
