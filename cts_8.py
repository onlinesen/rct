#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import subprocess
import time,sys,re
from subprocess import PIPE
import tkinter.filedialog
import tkinter.messagebox
from PIL import Image
import aircv as ac
import cv2
import numpy as np
import GetMainColor
import videotest
from lib.imcp.mixin import DeviceMixin

SETTINGS = "android"  # 原生:android; myos4:myos
CAMERA = "com.myos.camera"  # camera 包名
BLUE_NAME = "K300AG"  # 蓝牙设备名称

COME_TO = {
    "myos": {"Main": "Network & Internet", "Net": "Network", "Password": "Security",
             "Trust agents": "Security",
             "administrators": ["Security", "Device admin apps"],
             "appinfo": ["Apps & notifications", "See all"]},
    "android": {"Main": "Battery", "Net": "Network & Internet", "Password": "Security","Location": ["Security", "Location"],
                "Trust agents": ["Security & location"],
                "administrators": ["Security", "Device admin apps"]}}

import aircv as ac
import unittest
from uiautomator import Device

def getAdb():
    try:
        serial = []
        p = subprocess.Popen("adb devices", shell=True, stdout=PIPE, stderr=PIPE)
        out = p.stdout.readlines()
        for i in range(len(out)):
            if "List" in out[i]:
                continue
            if len(out[i]) > 5:
                serial.append(out[i].split()[0])
        return serial
    except Exception, e:
        import traceback
        traceback.print_exc()
        print u"设备没找到"
        sys.exit(1)


device = getAdb()
class CTSTest(unittest.TestCase):
    def setUp(self):
        try:
            try:
                self.serial = "5830b2e7"#device[0]
                self.d = Device(self.serial)
                print "device:",self.serial
            except Exception,e:
                self.d = Device(self.serial)
            #self.someback()
            cmds = ['adb'] + ['-s'] + [self.serial] + ['shell', 'getprop', 'ro.build.product']
            p = subprocess.Popen(cmds, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.model = p.communicate()[0].strip()
            cmds = ['adb'] + ['-s'] + [self.serial] + ['shell', 'wm', 'size']
            p = subprocess.Popen(cmds, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out = p.communicate()[0]
            self.wmsize = out.split()[-1].split("x")

            self.real_hight = self.d.info["displayHeight"]
            #self.isLocked()
            self.watch()
            self.startapp("com.android.cts.verifier", "com.android.cts.verifier.CtsVerifierActivity")
           # time.sleep(2)
           #  for i in xrange(0, 9):
           #      if "packageinstaller" in self.getPackage()[0]:
           #          self.d(className="android.widget.Button")[1].click()
           #      else:
           #          break
           #  print "setup ok"
        except Exception,e:
            print e.message

    def clear_notification(self):
        self.d.open.notification()
        if self.d(text="DECLINE").exists:
            self.d(text="DECLINE").click()
            time.sleep(1)
        if self.d(text="CLEAR ALL").exists:
            self.d(text="CLEAR ALL").click()
        else:
            for i in xrange(0,5):
                if self.d(resourceId="android:id/title").exists:
                    self.d(resourceId="android:id/title").swipe.right()
                    time.sleep(1)
            self.d.press.back()
        time.sleep(2)

    def miniscreenShot(self):
        try:
            out = \
                self.raw_cmd('shell', 'LD_LIBRARY_PATH=/data/local/tmp', '/data/local/tmp/minicap', '-i')
            m = re.search('"width": (\d+).*"height": (\d+).*"rotation": (\d+)', out, re.S)
            w, h, r = map(int, m.groups())
            w, h = min(w, h), max(w, h)
            #params = '{x}x{y}@{x1}x{y1}/{r}'.format(x=w, y=h, x1=w, y1=h, r=r)



            params = '{x}x{y}@{x1}x{y1}/{r}'.format(x=self.wmsize[0], y=self.wmsize[1], x1=self.wmsize[0], y1=self.wmsize[1], r=r)
            os.system('adb -s '+self.serial + ' shell \"LD_LIBRARY_PATH=/data/local/tmp /data/local/tmp/minicap -P %s' % params +' -S -s > /sdcard/ctstmp.png \"')
            os.system('adb -s ' + self.serial + ' pull /sdcard/ctstmp.png ./')
        except Exception, e:
            pass

    def findImage(self,img, tw=10):
        imgfound = [None, None]
        imobj = ac.imread(os.getcwd() + "/android-cts-verifier_8.1/" + img)
        for i in xrange(0, tw):
            try:
                self.miniscreenShot()
                time.sleep(1)
                imsrc = ac.imread(os.getcwd() + "/ctstmp.png")
                rt = ac.find_sift(imsrc, imobj)
                print "founding....:", rt
                if len(rt)>0 :
                   cof = float(rt['confidence'][0]) / rt['confidence'][1]
                   print "cof:",cof
                   if cof >0.6:
                       if rt['result'][0] >1 and rt['result'][1]>1:
                           if int(rt['result'][0]) < int(self.wmsize[0]) and rt['result'][1] <int(self.wmsize[1]):
                               print "founded:",rt
                               return rt['result']

            except Exception, e:
                #import traceback
                #print "e.mess:",e.message
                continue
                #return imgfound
        time.sleep(1)
        return imgfound

    def find_template(self, img, threshold=0.5, rgb=False, wt=10):
        """函数功能：找到最优结果."""
        im_search = ac.imread(os.getcwd() + "/android-cts-verifier_8.1/" +img.decode('u8').encode('gbk'))

        for i in xrange(0, wt):
            try:
                self.miniscreenShot()
                # 第一步：校验图像输入
                im_source = ac.imread(os.getcwd() + "/ctstmp.png")
                self.check_source_larger_than_search(im_source, im_search)
                # 第二步：计算模板匹配的结果矩阵res
                res = self._get_template_result_matrix(im_source, im_search)
                # 第三步：依次获取匹配结果
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
                h, w = im_search.shape[:2]
                # 求取可信度:
                confidence = self._get_confidence_from_matrix(im_source, im_search, max_loc, max_val, w, h, rgb)
                # 求取识别位置: 目标中心 + 目标区域:
                middle_point, rectangle = self._get_target_rectangle(max_loc, w, h)
                best_match = self.generate_result(middle_point, rectangle, confidence)
                print ("threshold=%s, result=%s" % (threshold, best_match))
                if best_match['result'][0] >= 1 and best_match['result'][1] >= 1 and confidence >= threshold:
                    # imgfound = (
                    #     best_match['rectangle'][0][0], best_match['rectangle'][0][1], best_match['rectangle'][2][0],
                    #     best_match['rectangle'][2][1])
                    imgfound = ((best_match['rectangle'][0][0] + (best_match['rectangle'][2][0] -best_match['rectangle'][0][0])/2),(best_match['rectangle'][0][1] + (best_match['rectangle'][1][1] -best_match['rectangle'][0][1])/2))
                    return imgfound if confidence >= threshold else None
            except Exception, e:
                return None

        return None

    # return {'confidence': 0.9968975186347961, 'result': (58, 127), 'rectangle': ((22, 97), (22, 158), (94, 158), (94, 97))}

    def check_source_larger_than_search(self, im_source, im_search):
        """检查图像识别的输入."""
        # 图像格式, 确保输入图像为指定的矩阵格式:
        # 图像大小, 检查截图宽、高是否大于了截屏的宽、高:
        h_search, w_search = im_search.shape[:2]
        h_source, w_source = im_source.shape[:2]
        if h_search > h_source or w_search > w_source:
            print "error"
    def generate_result(self, middle_point, pypts, confi):
        """
        Format the result: 定义图像识别结果格式
        """
        ret = dict(result=middle_point,
                   rectangle=pypts,
                   confidence=confi)
        return ret

    def _get_template_result_matrix(self, im_source, im_search):
        """求取模板匹配的结果矩阵."""
        # 灰度识别: cv2.matchTemplate( )只能处理灰度图片参数
        s_gray, i_gray = self.img_mat_rgb_2_gray(im_search), self.img_mat_rgb_2_gray(im_source)
        return cv2.matchTemplate(i_gray, s_gray, cv2.TM_CCOEFF_NORMED)

    def _get_target_rectangle(self, left_top_pos, w, h):
        """根据左上角点和宽高求出目标区域."""
        x_min, y_min = left_top_pos
        # 中心位置的坐标:
        x_middle, y_middle = int(x_min + w / 2), int(y_min + h / 2)
        # 左下(min,max)->右下(max,max)->右上(max,min)
        left_bottom_pos, right_bottom_pos = (x_min, y_min + h), (x_min + w, y_min + h)
        right_top_pos = (x_min + w, y_min)
        # 点击位置:
        middle_point = (x_middle, y_middle)
        # 识别目标区域: 点序:左上->左下->右下->右上, 左上(min,min)右下(max,max)
        rectangle = (left_top_pos, left_bottom_pos, right_bottom_pos, right_top_pos)

        return middle_point, rectangle

    def _get_confidence_from_matrix(self, im_source, im_search, max_loc, max_val, w, h, rgb):
        """根据结果矩阵求出confidence."""
        # 求取可信度:
        if rgb:
            # 如果有颜色校验,对目标区域进行BGR三通道校验:
            img_crop = im_source[max_loc[1]:max_loc[1] + h, max_loc[0]: max_loc[0] + w]
            confidence = self.cal_rgb_confidence(img_crop, im_search)
        else:
            confidence = max_val
        return confidence

    def cal_rgb_confidence(self, img_src_rgb, img_sch_rgb):
        """同大小彩图计算相似度."""
        # BGR三通道心理学权重:
        weight = (0.114, 0.587, 0.299)
        src_bgr, sch_bgr = cv2.split(img_src_rgb), cv2.split(img_sch_rgb)

        # 计算BGR三通道的confidence，存入bgr_confidence:
        bgr_confidence = [0, 0, 0]
        for i in range(3):
            res_temp = cv2.matchTemplate(src_bgr[i], sch_bgr[i], cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res_temp)
            bgr_confidence[i] = max_val

        # 加权可信度
        weighted_confidence = bgr_confidence[0] * weight[0] + bgr_confidence[1] * weight[1] + bgr_confidence[2] * \
                                                                                              weight[2]
        # 只要任何一通道的可信度低于阈值,均视为识别失败, 所以也返回每个通道的
        return weighted_confidence, bgr_confidence

    def img_mat_rgb_2_gray(self, img_mat):
        """
            turn img_mat into gray_scale, so that template match can figure the img data.
            "print(type(im_search[0][0])")  can check the pixel type.
        """
        assert isinstance(img_mat[0][0], np.ndarray), "input must be instance of np.ndarray"
        return cv2.cvtColor(img_mat, cv2.COLOR_BGR2GRAY)

    def clicktext(self,method="text",text=""):
        try:
            if method=="text":
                self.d(text=text).click()
                time.sleep(1)
            elif method == "textStartsWith":
                self.d(textStartsWith=text).click()
                time.sleep(1)
            return True
        except Exception,e:
            return False

    def isLocked(self):
        cmds = ['adb'] + ['-s'] + [self.serial] + ['shell', 'dumpsys', 'window', 'policy', '|grep', 'isStatusBarKeyguard']
        islock = subprocess.Popen(cmds, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()[0]
        if "=true" in islock:
            self.d.wakeup()
            self.d.swipe(500, 700, 500, 100, steps=20)
            time.sleep(1)
            self.raw_cmd('shell', 'input', 'text', '1111')
            time.sleep(1)
            self.raw_cmd('shell', 'input', 'keyevent', '66')
            time.sleep(1)
            self.d.press.home()
            if self.getPackage()[0]==None:
                self.raw_cmd('shell', 'input', 'text', '1111')
                time.sleep(0.5)
                self.raw_cmd('shell', 'input', 'keyevent', '66')
                time.sleep(1)

            elif "aunche" in self.getPackage()[0]:
                return True
            else:
                self.raw_cmd('shell', 'input', 'text', '1111')
                time.sleep(0.5)
                self.raw_cmd('shell', 'input', 'keyevent', '66')
                time.sleep(1)
                if "aunche" in self.getPackage()[0]:
                    return True
        else:
            return True

    def tearDown(self):
        self.d.press.back()
        self.d.press.back()
        self.d.press.home()

    def back2Verify(self):
        self.d.press.recent()
        time.sleep(1)
        self.d(text="CTS Verifier").click()
        time.sleep(1)

    def gototext(self, dct):
        goto_dct = dct  # ["a","a1"]
        for i in goto_dct:
            self.findtext(i)

    def removepassword(self):
        try:
            self.startapp("com.android.settings","com.android.settings.Settings")
            time.sleep(1)
            self.d(scrollable=True).scroll.to(textStartsWith="Security")
            self.d(textStartsWith="Security").click()
            # self.findtext(COME_TO[SETTINGS]["Password"])
            print "remove pwd..."
            self.d(text="Screen lock").click()
            time.sleep(2)
            if self.d(text="Re-enter your password").exists:
                self.raw_cmd('shell', 'input', 'text', '1111')
                time.sleep(1)
                self.raw_cmd('shell', 'input', 'keyevent', '66')
                time.sleep(2)
                self.d(text="None").click()
                time.sleep(0.5)
                self.d(textContains="YES").click()
                time.sleep(1)
            elif self.d(text="Re-enter your PIN").exists:
                self.raw_cmd('shell', 'input', 'text', '1111')
                time.sleep(1)
                self.raw_cmd('shell', 'input', 'keyevent', '66')
                time.sleep(2)
                self.d(text="None").click()
                time.sleep(0.5)
                self.d(textContains="YES").click()
            time.sleep(1)
        except Exception,e:
            pass

    def getPackage(self):
        try:
            out = self.raw_cmd('shell', 'getprop', 'ro.build.version.sdk')
            sdk = int(out.strip())
            if sdk < 26:
                getp = self.raw_cmd('shell', 'dumpsys', 'activity', '|grep', 'mFocusedActivity')
            else:
                getp = self.raw_cmd('shell', 'dumpsys', 'activity', '|grep', 'mResumedActivity')
            if "com" in getp:  # out = self.raw_cmd( 'shell', 'ps', '|grep', 'minicap')
                start = getp.find("com")
                end = getp.find('/')
                package = getp[start:end].strip()
                endactivty = getp[start:].strip()  # "com.android.setings/.abcdef xyszn"
                endactivty1 = endactivty.find(" ")  #
                aend = endactivty[:endactivty1].strip("\r\n")  # "com.android.setings/.abcdef"

                if "/." in aend:
                    # activity = aend.replace("/.", "/" + package + ".")
                    activity = package + aend.split("/")[1]
                elif "/" in aend:
                    activity = aend.split("/")[1]
                return package, activity
            else:
                return None, None
        except Exception, e:
            return None, None

    def raw_cmd(self, *args):
        cmds = ['adb'] + ['-s'] + [self.serial] + list(args)
        p = subprocess.Popen(cmds, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        c = p.communicate()[0]
        return c

    def startapp(self, pkg,activiy=None):
        if activiy==None:
            os.system('adb -s '+self.serial + ' shell monkey -p '+ pkg+ ' -c android.intent.category.LAUNCHER 1')
        else:
            os.system('adb -s '+self.serial + ' shell am start '+ pkg+ '/'+activiy)
        time.sleep(2)
        if self.getPackage()[0] != None:
            for i in xrange(0, 8):
                if "packageinstaller" in self.getPackage()[0]:
                    self.d(className="android.widget.Button")[1].click()
                else:
                    break
        print "start:", pkg

    def findtext(self, text):
        try:
            time.sleep(1)
            if self.d(resourceId="android:id/list").exists:
                self.d(resourceId="android:id/list").scroll.to(textStartsWith=text)
            else:
                self.d(scrollable=True).scroll.to(textStartsWith=text)
            time.sleep(2)
            self.d(textStartsWith=text).click()
            time.sleep(1)
            return True
        except Exception, e:
            if "SCROLLABLE=true" in e.message:
                try:
                    self.d(textStartsWith=text).click()
                except Exception, e:
                    return False
                return True
            else:
                return False
        finally:
            time.sleep(1)

    def compareImage(self, i1, i2, bc="Camera 0"):

        # print i1, i2, bc
        otcimage = videotest.OTCImage(self.serial)
        b = self.d(resourceId=i1).info["bounds"]
        box = (b["left"], b["top"], b["right"], b["bottom"])
        # box=(0,253,796,850)
        # print box

        self.miniscreenShot()
        img = Image.open("ctstmp.png")
        img_0 = img.crop(box)

        b = self.d(resourceId=i2).info["bounds"]
        box2 = (b["left"], b["top"], b["right"], b["bottom"])
        #box2 = (box[2],box[1],box[2]*2,box[3])
        #self.miniscreenShot()
        img_1 = img.crop(box2)
        if bc == "Camera 1":
            img_1 = img_1.transpose(Image.FLIP_LEFT_RIGHT)
        ssim = float(otcimage.calc_similar(img_0, img_1))
        return ssim

    def press_pass(self, tof=True):
        try:
            time.sleep(3)
            if tof:
                if self.d(resourceId="com.android.cts.verifier:id/pass_button").info["enabled"]:
                    self.d(resourceId="com.android.cts.verifier:id/pass_button").click()
                else:
                    self.d(resourceId="com.android.cts.verifier:id/fail_button").click()
            else:
                self.d(resourceId="com.android.cts.verifier:id/fail_button").click()
        except Exception, e:
            return 0
        finally:
            time.sleep(2)

    def test_CameraFormatTest(self):
        self.d.watchers.run()
        print "test_CameraFormatTest..."
        chl = ["NV21", "YV12"]
        cam = ["Camera 0", "Camera 1"]
        self.startapp("com.android.cts.verifier", "com.android.cts.verifier.CtsVerifierActivity")
        time.sleep(2)
        res =[]
        if not (self.findtext("Camera Formats")):
            print "no camera formats found!"
            return 0
        # res = RESOLUTION[self.model]
        #out = self.raw_cmd('shell', 'dumpsys','media.camera','|grep','preview-size-values','|head -n 1').split()[1]

        self.d(resourceId="com.android.cts.verifier:id/resolution_selection").click()
        time.sleep(2)
        for j in xrange(0,5):
            tv = self.d(className="android.widget.TextView")
            for i in xrange(0,tv.count):
                if str(tv[i].text) not in res:
                    res.append(str(tv[i].text))
                    print str(tv[i].text)
            self.d(scrollable=True).scroll(steps=50)
            time.sleep(2)
        self.d.press.back()

        for j in cam:
            print j
            self.d(resourceId="com.android.cts.verifier:id/cameras_selection").click()
            if not (self.findtext(j)):
                print "no", j, "found!"
                self.d.press.back()
                continue
            for k in chl:
                print k
                self.d(resourceId="com.android.cts.verifier:id/format_selection").click()
                if not (self.findtext(k)):
                    print "no", k, "found!"
                    self.d.press.back()
                    continue
                for i in res:
                    print i
                    self.d(resourceId="com.android.cts.verifier:id/resolution_selection").click()
                    if not (self.findtext(i)):
                        print "no", i, "found!"
                        self.d.press.back()
                        continue
                        # ssim = self.compareImage("com.android.cts.verifier:id/preview_view",
                        #                          "com.android.cts.verifier:id/format_view", "Camera 0")
                        # print i, ssim
                        # if ssim<0.6:
                        #     print i,ssim
                        #     result = False
        self.press_pass()

    def test_CameraITSTest(self):
        self.d.watchers.run()
        if not (self.findtext("Camera ITS Test")):
            print "no camera its found!"
            return 0

    def watch(self):
        self.d.watcher("AUTO_OK").when(resourceId="android:id/button1").when(text="OK") \
            .click(text="OK")
        self.d.watcher("ACTION_OK").when(resourceId="android:id/icon").when(text="CTS Verifier") \
            .click(text="CTS Verifier")
        self.d.watcher("SIM_OK").when(text="No SIM card").press.back()
        self.d.watcher("permission").when(text="ACCEPT").click(text="ACCEPT")
        self.d.watchers.run()

    def setpassword(self, method, pwd):
        self.d(scrollable=True).fling.toBeginning()
        time.sleep(1)
        if not self.d(textStartsWith="Screen lock").exists:
            print "Screen lock not exist "
            self.findtext(COME_TO[SETTINGS]["Password"])
        if self.d(textStartsWith="Screen lock").exists:
                self.d(textStartsWith="Screen lock").click()
        if self.d(textStartsWith="Screen lock").exists:
                self.d(textStartsWith="Screen lock").click()
        time.sleep(1)
        if self.d(textStartsWith="Confirm").exists or self.d(textStartsWith="Re-enter").exists:
            if method == "Password" and self.d(textStartsWith="Re-enter your PIN").exists:
                self.raw_cmd('shell', 'input', 'text', '1111')
                time.sleep(1)
                self.raw_cmd('shell', 'input', 'keyevent', '66')
                time.sleep(1)
                self.d(text="Password").click()
                time.sleep(1)
                if self.d(text="Secure start-up").exists:
                    self.d(text="YES").click()
                if self.d(text="Require password to start device").exists:
                    self.d(text="Require password to start device").click()
                self.d(resourceId="com.android.settings:id/password_entry").set_text(pwd)
                self.d(resourceId="com.android.settings:id/next_button").click()
                self.d(resourceId="com.android.settings:id/password_entry").set_text(pwd)
                self.d(resourceId="com.android.settings:id/next_button").click()
                self.d(text="DONE").click()
            elif method == "PIN" and self.d(textStartsWith="Re-enter your password").exists:
                self.raw_cmd('shell', 'input', 'text', '1111')
                time.sleep(1)
                self.raw_cmd('shell', 'input', 'keyevent', '66')
                time.sleep(1)
                self.d(text="PIN").click()
                time.sleep(1)
                if self.d(text="Secure start-up").exists:
                    self.d(text="YES").click()
                time.sleep(1)
                self.raw_cmd('shell', 'input', 'text', '1111')
                time.sleep(1)
                self.raw_cmd('shell', 'input', 'keyevent', '66')
                time.sleep(1)
                self.raw_cmd('shell', 'input', 'text', '1111')
                time.sleep(1)
                self.raw_cmd('shell', 'input', 'keyevent', '66')
                time.sleep(1)
            else:
                self.back2Main()
        else:
            if method == "Password":
                self.d(text="Password").click()
                time.sleep(1)
                if self.d(text="Secure start-up").exists:
                    self.d(text="YES").click()

                if self.d(text="Require password to start device").exists:
                    self.d(text="Require password to start device").click()
                if self.d(text="OK").exists:
                    self.d(text="OK").click()
                self.raw_cmd('shell', 'input', 'text', '1111')
                time.sleep(1)
                self.raw_cmd('shell', 'input', 'keyevent', '66')
                time.sleep(1)
                self.raw_cmd('shell', 'input', 'text', '1111')
                time.sleep(1)
                self.raw_cmd('shell', 'input', 'keyevent', '66')
                time.sleep(1)
                if self.d(text="DONE").exists:
                    self.d(text="DONE").click()
                if self.d(textStartsWith="YES").exists:
                    self.d(textStartsWith="YES").click()
            elif method == "PIN":
                self.d(text="PIN").click()
                time.sleep(1)
                if self.d(text="Secure start-up").exists:
                    self.d(text="YES").click()
                if self.d(text="Require PIN to start device").exists:
                    self.d(text="Require PIN to start device").click()

                self.d(resourceId="com.android.settings:id/password_entry").set_text(pwd)
                self.d(resourceId="com.android.settings:id/next_button").click()
                self.d(resourceId="com.android.settings:id/password_entry").set_text(pwd)
                self.d(resourceId="com.android.settings:id/next_button").click()
                self.d(text="DONE").click()
        self.back2Main()

    def back2Main(self):
        for i in xrange(0, 4):
            act = self.getPackage()[1]
            print "act:",act
            if "com.android.settings.Settings" == act or "com.android.cts.verifier" in act:
                break
            else:
                self.d.press.back()
                time.sleep(2)

    def startcamera(self, act):
        self.raw_cmd('shell', 'am', 'start', '-a', 'android.media.action' + act)

    def test_CameraIntentTest(self):
        self.raw_cmd('shell', 'pm', 'clear', CAMERA)
        print "test_CameraIntentTest"
        if not (self.findtext("Camera Intents")):
            print "no camera Intents found!"
            return 0
        self.d(text="START TEST").click()
        self.d.press.home()
        time.sleep(1)
        # self.startcamera(".STILL_IMAGE_CAMERA")
        self.startapp(CAMERA)
        time.sleep(1)
        if self.d(text="GOT IT").exists:
            self.d(text="GOT IT").click()
        time.sleep(1)
        if self.d(text="Got it").exists:
            self.d(text="Got it").click()
        time.sleep(1)
        if self.d(text="ACCEPT").exists:
            self.d(text="ACCEPT").click()
        time.sleep(1)
        if self.d(text="SKIP").exists:
            self.d(text="SKIP").click()
        if self.d(text="GOT IT").exists:
            self.d(text="GOT IT").click()
        time.sleep(1)
        if self.d(text="PHOTO").exists:
            self.d(text="PHOTO").click()
        for i in xrange(0, 4):
            time.sleep(5)
            self.raw_cmd('shell', 'input', 'keyevent', '27')
        self.d.press.back()
        self.back2Verify()
        print "camera over"
        self.press_pass()

        # start video
        self.d(text="START TEST").click()
        time.sleep(1)
        self.d.press.home()
        time.sleep(1)
        # self.startcamera(".VIDEO_CAPTURE")
        self.startapp("com.myos.camera")
        time.sleep(2)
        if self.d(text="PHOTO").exists:
            self.d(text="VIDEO").click()
        else:
            self.d(scrollable=True).fling.horiz.backward()
        time.sleep(1)
        for i in xrange(0, 2):
            time.sleep(10)
            self.raw_cmd('shell', 'input', 'keyevent', '27')
        self.d.press.back()
        self.back2Verify()
        time.sleep(1)
        self.press_pass()
        print "video over"

        # intent camera
        print "intent camera..."
        self.d(text="START TEST").click()
        time.sleep(2)
        self.raw_cmd('shell', 'input', 'keyevent', '27')
        time.sleep(4)
        self.d(resourceId="com.myos.camera:id/switch_camera_facing").click()
        #self.d.click(int(self.wmsize[0]) * 0.8, int(self.real_hight) - 50)
        time.sleep(3)
        self.press_pass()
        print "inetnt camera over"

        # intent video
        self.d(text="START TEST").click()
        time.sleep(2)
        self.raw_cmd('shell', 'input', 'keyevent', '27')
        time.sleep(6)
        self.raw_cmd('shell', 'input', 'keyevent', '27')
        time.sleep(2)
        #self.d.click(int(self.wmsize[0]) * 0.8, int(self.real_hight) - 50)
        self.d(resourceId="com.myos.camera:id/btn_done").click()
        time.sleep(1)
        self.press_pass()

    def test_CameraOrientation(self):
        print "test_CameraOrientation"
        if not (self.findtext("Camera Orientation")):
            print "no camera Orientation found!"
            return 0
        for i in xrange(0, 8):
            time.sleep(2)
            if self.d(text="TAKE PHOTO").info["enabled"]:
                self.d(text="TAKE PHOTO").click()
                time.sleep(2)
                ssim = self.compareImage("com.android.cts.verifier:id/camera_view",
                                         "com.android.cts.verifier:id/format_view", "Camera 0")
                print "compare result:",ssim
                if ssim > 0.5:
                    self.press_pass()
                else:
                    self.press_pass(tof=False)
                    break

    def test_CameraVideo(self):
        print "test_CameraVideo"
        if not (self.findtext("Camera Video")):
            print "no camera Orientation found!"
            return 0
        cam = ["Camera 0", "Camera 1"]
        leve = ["LOW", "HIGH", "QCIF", "QVGA", "CIF", "480P", "720P", "1080P"]
        result = True
        for j in cam:
            print j
            self.d(resourceId="com.android.cts.verifier:id/cameras_selection").click()
            if not (self.findtext(j)):
                print "no", j, "found!"
                self.d.press.back()
                continue
            for k in leve:
                print k
                time.sleep(0.5)
                if self.d(resourceId="com.android.cts.verifier:id/resolution_selection").exists:
                    self.d(resourceId="com.android.cts.verifier:id/resolution_selection").click()
                    time.sleep(1)
                if not (self.findtext(k)):
                    print "no", k, "found!"
                    continue
                if self.d(text="TEST").info["enabled"]:
                    self.d(text="TEST").click()
                    time.sleep(6)
                    self.d(text="Ready").wait.exists(timeout=3000)
        self.press_pass()

    def test_CarDock(self):
        print "test_CarDock"
        if not (self.findtext("Car Dock Test")):
            print "no Car Dock found!"
            return 0
        self.d(text="ENABLE CAR MODE").click()
        time.sleep(2)
        if self.d(text="Complete action using CTS Verifier").exists:
            self.d(text="JUST ONCE").click()
        elif self.d(text="Complete action using").exists:
            self.d(text="CTS Verifier").click()
            time.sleep(1)
            self.d(text="JUST ONCE").click()
            time.sleep(1)

        time.sleep(2)

        if self.d(text="ENABLE CAR MODE").exists:
            self.d(text="ENABLE CAR MODE").click()
        if self.d(text="Complete action using CTS Verifier").exists:
            self.d(text="JUST ONCE").click()
        elif self.d(text="Complete action using").exists:
            self.d(text="CTS Verifier").click()
            time.sleep(1)
            self.d(text="JUST ONCE").click()
            time.sleep(1)

        if self.d(text="Press the Home button").wait.exists(timeout=1000):
            self.d.press.home()
            time.sleep(1)
            if self.d(text="Complete action using CTS Verifier").exists:
                self.d(text="JUST ONCE").click()
            else:
                self.d(text="CTS Verifier").click()

        time.sleep(5)

    def test_Alarms(self):
        print "test_Alarms"
        if not (self.findtext("Alarms and Timers Tests")):
            print "no Alarms found!"
            return 0
        # show alarm
        self.d(text="Show Alarms Test").click()
        self.d(text="SHOW ALARMS").click()
        pkg = self.getPackage()[0]
        time.sleep(2)
        self.d.press.back()
        if pkg == "com.android.deskclock":
            result = True
            self.press_pass()
        else:
            self.press_pass(tof=False)
        print "Set Alarm Test"

        # set alarm
        result0 = False
        self.d(text="Set Alarm Test").click()
        self.d(text="SET ALARM").click()
        time.sleep(1)
        act = self.getPackage()[0]
        self.d.press.back()
        self.d.press.back()
        if act == "com.android.deskclock":
            result0 = True
            self.press_pass()
        else:
            self.press_pass(tof=False)

        print "Start Alarm Test"
        # start alarm
        result1 = False
        self.d(text="Start Alarm Test").click()
        time.sleep(1)
        self.d(text="SET ALARM").click()
        time.sleep(2)
        self.d(text="VERIFY").click()
        if self.d(text="Start Alarm Test").wait.exists(timeout=1000):
            result1 = True
            self.d.press.back()
        if self.d(text="DISMISS").wait.exists(timeout=120000):
            result1 = result1 & True
            self.d(text="DISMISS").click()
        if result1:
            self.press_pass()
        else:
            self.press_pass(tof=False)

        # # start alarm
        # print "Full Alarm Test"
        # result = False
        # self.d(text="Full Alarm Test").click()
        # self.d(text="CREATE ALARM").click()
        # result = self.d(text="01:23").wait.exists(timeout=1000)
        # self.d(text="01:23").click()
        # result = result & self.d(text="Create Alarm Test").wait.exists(timeout=1000)
        # result = result & self.d(text="Mon, Wed").wait.exists(timeout=1000)
        # result = result & self.d(text="Snoozed").right(resourceId="com.android.deskclock:id/set_switch").info["checked"]
        # result = result & self.d(text="Vibrate").right(resourceId="com.android.deskclock:id/set_switch").info["checked"]
        # self.d.press.back()
        # self.d.press.back()
        # if result:
        #     self.press_pass()
        # else:
        #     self.press_pass(tof=False)

        # start alarm
        print "Full Alarm Test"
        result2 = False
        self.d(text="Full Alarm Test").click()
        time.sleep(1)
        self.d(text="CREATE ALARM").click()
        result2 = self.d(text="01:23").wait.exists(timeout=1000)
        self.d(text="01:23").click()

        result2 = result2 & self.d(text="Create Alarm Test").wait.exists(timeout=1000)
        result2 = result2 & (self.d(textStartsWith="Mon, Wed").exists or (self.d(text="M").checked and self.d(text="W").checked ))
        result2 = result2 & self.d(text="Silent").exists
        result2 = result2 & self.d(text="Vibrate").checked

        print "result2:",result2
        self.d.press.back()
        if result2:
            self.press_pass()
        else:
            self.press_pass(tof=False)

        # Set timer
        print "Set Alarm Test"
        result3 = False
        self.d(text="Set Timer Test").click()
        self.d(text="SET TIMER").click()
        pkg = self.getPackage()[0]
        self.d.press.back()
        if pkg == "com.android.deskclock":
            result3 = True
            self.press_pass()
        else:
            self.press_pass(tof=False)

        # start timer
        print "Start Timer Test"
        result4 = False
        self.d(text="Start Timer Test").click()
        self.d(text="START TIMER").click()
        time.sleep(1)
        if self.d(text="STOP").wait.exists(timeout=120000):
            self.d(text="STOP").click()
        if "com.android.cts.verifier" in self.getPackage()[0]:
            self.press_pass()
        else:
            self.press_pass(tof=False)

        # start timer ui
        result5 = False
        self.d(text="Start Timer With UI Test").click()
        self.d(text="START TIMER").click()
        time.sleep(2)
        pkg = self.getPackage()[0]
        self.d.press.back()
        if pkg == "com.android.deskclock":
            result5 = True
        if self.d(text="STOP").wait.exists(timeout=50000):
            self.d(text="STOP").click()
        time.sleep(2)
        result5 = result5 & self.d(text="START TIMER").exists
        if result5:
            self.press_pass()
        else:
            self.press_pass(tof=False)
        time.sleep(2)
        self.press_pass()

    def test_DeviceAdmin(self):
        print "test_DeviceAdmin"
        if not (self.findtext("Device Admin Tapjacking Test")):
            print "no Admin Tapjacking found!"
            return 0
        self.d(text="ENABLE DEVICE ADMIN").click()
        time.sleep(3)
        self.d.press.back()
        self.d.press.back()
        if not self.d(text="ENABLE DEVICE ADMIN").info["enabled"]:
            self.press_pass()
        else:
            self.press_pass(tof=False)

    def test_Keyguard(self):
        self.d.watchers.run()
        self.startapp("com.android.cts.verifier", "com.android.cts.verifier.CtsVerifierActivity")
        time.sleep(2)
        print "test_Keyguard"
        if not (self.findtext("Keyguard Disabled Features Test")):
            print "no Keyguard found!"
            return 0
        time.sleep(1)
        self.startapp("com.android.settings","com.android.settings.Settings")
        self.gototext(COME_TO[SETTINGS]["administrators"])
        time.sleep(1)
        ct = self.d(text="CTS Verifier").count
        for i in xrange(0, ct):
            self.d(text="CTS Verifier")[i].right(resourceId="com.android.settings:id/checkbox").click()
            if not self.findtext("Activate this device"):
                self.d.press.back()
                break
            time.sleep(1)

        self.back2Main()
        self.setpassword("Password", "1111")
        self.d.press.back()
        time.sleep(1)

        self.d(text="PREPARE TEST").click()
        time.sleep(1)
        self.startapp("com.android.settings","com.android.settings.Settings")
        self.gototext(COME_TO[SETTINGS]["Trust agents"])
        self.findtext("Trust agents")
        time.sleep(1)
        ass3_result = False
        if not self.d(resourceId="android:id/title").enabled:
            time.sleep(2)
            ass3_result = (self.findImage("trustagents.720x1440.png") != None)
            self.d.press.back()


        self.back2Main()
        if self.d(text="Battery").exists:
            self.d(textStartsWith="Screen lock").click()
        self.findtext("Fingerprint")
        self.d(resourceId="android:id/list").child(text="Fingerprint").click()
        time.sleep(1)
        ass1_result = ("t use your" in self.d(resourceId="com.android.settings:id/description_text").text)
        self.back2Main()
        self.d.press.back()
        time.sleep(1)
        self.d(text="Fingerprint is disabled in Settings").click()
        time.sleep(1)
        if ass1_result:
            self.d(text="PASS").click()
        else:
            self.d(text="FAIL").click()
        time.sleep(4)

        # assert 2
        self.d(text="Fingerprint disabled on keyguard").click()
        self.d(text="PASS").click()

        # time.sleep(1)
        # if tkinter.messagebox.askokcancel('提示', '锁屏，用指纹登陆，成功点确定，不成功点取消'):
        #     self.d(text="PASS").click()
        # else:
        #     self.d(text="FAIL").click()
        time.sleep(5)

        # assert 3
        self.d(text="Disable trust agents").click()
        time.sleep(1)
        if ass3_result:
            self.d(text="PASS").click()
        else:
            self.d(text="FAIL").click()
        time.sleep(5)

        # assert 4
        self.d(text="Disable camera").click()
        time.sleep(1)
        self.d(text="GO").click()
        time.sleep(1)
        self.startapp("com.myos.camera")
        self.d.wakeup()
        assert4 = not self.getPackage()[0] == "com.myos.camera"
        self.d.swipe(500, 700, 500, 100, steps=20)
        time.sleep(1)
        self.raw_cmd('shell', 'input', 'text', '1111')
        time.sleep(0.5)
        self.raw_cmd('shell', 'input', 'keyevent', '66')
        time.sleep(1)
        if self.d(text="ALLOW").exists:
            self.d(text="ALLOW").click()
        if self.d(text="GOT IT").exists:
            self.d(text="GOT IT").click()
            time.sleep(1)
        if CAMERA == self.getPackage()[0]:
            self.d.press.back()
            time.sleep(2)
        if assert4:
            self.d(text="PASS").click()
        else:
            self.d(text="FAIL").click()
        time.sleep(4)
        # assert 5
        self.d(text="Disable notifications").click()
        time.sleep(1)
        self.d(text="GO").click()
        time.sleep(5)
        self.d.wakeup()
        time.sleep(1)
        self.d.swipe(500, 700, 500, 100, steps=10)
        time.sleep(1)
        self.raw_cmd('shell', 'input', 'text', '1111')
        time.sleep(0.5)
        self.raw_cmd('shell', 'input', 'keyevent', '66')
        time.sleep(0.5)
        self.d.open.notification()
        time.sleep(0.5)
        ass5_result = self.d(text="This is a notification").exists
        time.sleep(0.5)
        self.d.press.back()
        if ass5_result:
            self.d(text="PASS").click()
        else:
            self.d(text="FAIL").click()
        time.sleep(2)
        self.press_pass()
        self.removepassword()

    def test_Policy(self):
        result = True
        if not (self.findtext("Policy Serialization Test")):
            print "no Policy Serialization found!"
            return 0
        self.d(text="GENERATE POLICY").click()
        time.sleep(2)
        self.d(text="APPLY POLICY").click()
        time.sleep(2)

        self.findtext("Activate this device")

        self.raw_cmd('shell', 'reboot')
        time.sleep(50)
        try:
            print self.d.info
        except Exception,e:
            print self.d.info
        self.d.screen.on()
        if self.d(textStartsWith="No SIM").exists:
            self.d.press.back()
        self.d.press.back()
        self.isLocked()
        getp = self.raw_cmd('wait-for-device', 'shell', 'ls')
        if len(getp) > 1:
            self.d = Device(self.serial)
            self.watch()
            if self.d(text="No SIM card").exists:
                self.d.press.back()
                time.sleep(2)
            self.d.press.home()
            time.sleep(2)
            cmds = ['adb'] + ['-s'] + [self.serial] + ['shell', 'am', 'start', '-W',
                                                       'com.android.cts.verifier/.CtsVerifierActivity']
            # cmds = ['adb'] + ['-s'] + [serial] + ['shell', 'getprop', 'ro.vendor.product.model']
            p = subprocess.Popen(cmds, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
            time.sleep(3)

        if not (self.findtext("Policy Serialization Test")):
            print "no Keyguard found!"
            return 0
        time.sleep(2)

        for i in xrange(0, 4):
            b = self.d(resourceId="android:id/text1")[i].bounds
            box = ((b["right"]/2), b["top"], b["right"], b["bottom"])
            self.miniscreenShot()
            img = Image.open("ctstmp.png")
            img_0 = img.crop(box)
            img_0.show()
            color = GetMainColor.get_dominant_color(img_0)
            get = GetMainColor.min_color_diff(color)
            if len(get) == 2:
                result = result & (True if get[1] == "GREEN" else False)
                print get[1]
        if result:
            self.press_pass()
        else:
            self.press_pass(tof=False)

    def test_Redacted(self):
        print "test_Redacted"
        if not (self.findtext("Redacted Notifications Keyguard Disabled Features Test")):
            print "no Redacted found!"
            return 0
        self.startapp("com.android.settings","com.android.settings.Settings")
        self.back2Main()
        self.gototext(COME_TO[SETTINGS]["administrators"])
        time.sleep(1)
        ct = self.d(text="CTS Verifier").count
        for i in xrange(0, ct):
            self.d(text="CTS Verifier")[i].right(resourceId="com.android.settings:id/checkbox").click()
            if not self.findtext("Activate this device"):
                self.d.press.back()
                break
            time.sleep(1)
        self.back2Main()
        self.setpassword("Password", "1111")
        self.d.press.back()

        self.d(text="PREPARE TEST").click()
        time.sleep(1)
        self.d(text="Disable unredacted notifications").click()
        self.d(text="GO").click()
        time.sleep(2)
        self.d.wakeup()
        self.d.swipe(500, 700, 500, 100, steps=20)
        time.sleep(1)
        self.raw_cmd('shell', 'input', 'text', '1111')
        time.sleep(0.5)
        self.raw_cmd('shell', 'input', 'keyevent', '66')
        time.sleep(0.5)
        self.d.open.notification()
        time.sleep(0.5)
        ass_result = self.d(text="This is a notification").exists
        time.sleep(0.5)
        self.d.press.back()
        if ass_result:
            self.d(text="PASS").click()
        else:
            self.d(text="FAIL").click()
        time.sleep(2)
        self.press_pass()
        self.removepassword()

    def test_ScreenLock(self):

        self.startapp("com.android.cts.verifier", "com.android.cts.verifier.CtsVerifierActivity")
        time.sleep(2)
        print "test_ScreenLock"
        if not (self.findtext("Screen Lock Test")):
            print "no test_ScreenLock found!"
            return 0

        self.startapp("com.android.settings","com.android.settings.Settings")
        self.setpassword("Password", "1111")
        self.d.press.back()
        self.d(text="FORCE LOCK").click()
        time.sleep(1)
        if self.d(textStartsWith="Activate this device").exists:
            self.d(textStartsWith="Activate this device").click()
        self.d.wakeup()
        time.sleep(1)
        self.d.swipe(500, 700, 500, 100, steps=20)
        time.sleep(2)
        self.raw_cmd('shell', 'input', 'text', '1111')
        time.sleep(0.5)
        self.raw_cmd('shell', 'input', 'keyevent', '66')
        time.sleep(1)
        self.press_pass()
        time.sleep(1)
        self.removepassword()

    def test_Hardware(self):
        result = True
        self.startapp("com.android.cts.verifier", "com.android.cts.verifier.CtsVerifierActivity")
        time.sleep(2)
        print "test_Hardware"
        if not (self.findtext("Hardware/Software Feature Summary")):
            print "no Hardware found!"
            return 0
        time.sleep(2)
        count = self.d(resourceId="com.android.cts.verifier:id/fs_icon").count
        scrl = True
        scrl1 = 1
        while scrl and scrl1 <= 2:
            for j in xrange(0, count):
                b = self.d(resourceId="com.android.cts.verifier:id/fs_icon")[j].bounds
                box = (b["left"] + 10, b["top"] + 10, b["right"] - 10, b["bottom"] -10)
                self.miniscreenShot()
                img = Image.open("ctstmp.png")
                img_0 = img.crop(box)
                color = GetMainColor.get_dominant_color(img_0)
                get = GetMainColor.min_color_diff(color)
                if len(get) == 2:
                    result = result & (False if get[1] == "READ" else True)
            scrl = self.d(scrollable=True).scroll(steps=30)
            if not scrl:
                scrl1 = scrl1 + 1
            time.sleep(1)
            count = self.d(resourceId="com.android.cts.verifier:id/fs_icon").count
        if result:
            self.d(resourceId="com.android.cts.verifier:id/pass_button").click()
        else:
            self.d(resourceId="com.android.cts.verifier:id/fail_button").click()

    def test_Companion(self):
        print "test_Companion"
        if not (self.findtext("Companion Device Test")):
            print "no Companion found!"
            return 0
        time.sleep(2)
        self.d(text="GO").click()
        time.sleep(5)
        if self.d(text=BLUE_NAME).exists:
            self.d(text=BLUE_NAME).click()
        self.press_pass()

    def test_GNSS(self):
        print "test_GNSS"
        if not (self.findtext("GNSS Measurement Before Location Test")):
            print "no Location found!"
            return 0
        time.sleep(1)
        self.d(text="NEXT").click()
        time.sleep(5)
        self.d.press.back()
        time.sleep(2)
        gnss = ["GNSS Measurement Constellation Test", "GNSS Measurement Registration Test",
                "GNSS Measurement Values Test",
                "GNSS Navigation Message Test", "GNSS Pseudorange Test", "GNSS TTFF Test"]
        for i in gnss:
            if not (self.findtext(i)):
                print "no ", i, " found!"
                continue
            time.sleep(1)
            self.d(text="NEXT").click()
            time.sleep(2)
            for j in xrange(0, 20):
                time.sleep(20)
                en = "All test pass" in self.d(resourceId="com.android.cts.verifier:id/text").text
                if en:
                    break
            self.d.press.back()
        time.sleep(5)

    def test_USB(self):
        print "test_USB"
        if not (self.findtext("USB Accessory Test")):
            print "no USB found!"
            return 0
        time.sleep(2)
        self.startapp("com.android.cts.verifierusbcompanion")
        self.d(text="START DEVICE TEST COMPANION").click()
        time.sleep(5)

        if self.d(text=BLUE_NAME).exists:
            self.d(text=BLUE_NAME).click()
        self.press_pass()

    def AdminInsatll(self):  # 8.1 tcs
        self.d.watchers.run()
        print "test_AdminInsatll"
        os.system('adb -s '+self.serial +' install -r -t  android-cts-verifier_8.1/CtsEmptyDeviceAdmin.apk')

        if not (self.findtext("Device Admin Uninstall Test")):
            print "no Admin Uninstall found!"
            return 0
        time.sleep(0.5)
        if (self.d(text="ENABLE ADMIN").enable):
            self.d(text="ENABLE ADMIN").click()
            time.sleep(0.5)
            self.d(scrollable=True).fling.toEnd()
            self.d(textStartsWith="Activate this device admin app").click()
            time.sleep(0.5)
        self.d(text="LAUNCH SETTINGS").click()
        time.sleep(1)
        self.d(text="UNINSTALL").click()
        time.sleep(1)
        self.d(text="Deactivate & uninstall").click()
        self.findtext("OK")
        time.sleep(0.5)
        self.press_pass()

    def test_ConnectivityConstraints(self):
        try:
            result = True
            self.startapp("com.android.settings","com.android.settings.Settings")
            time.sleep(1)
            self.findtext(COME_TO[SETTINGS]["Net"])
            if self.d(resourceId="com.android.settings:id/switchWidget").checked:
                self.d(resourceId="com.android.settings:id/switchWidget").click()
                time.sleep(1)
            self.startapp("com.android.cts.verifier", "com.android.cts.verifier.CtsVerifierActivity")
            time.sleep(2)
            print "test_ConnectivityConstraints"
            if not (self.findtext("Connectivity Constraints")):
                print "no ConnectivityConstraints found!"
                return 0
            time.sleep(1)

            self.d(text="START TEST").click()
            time.sleep(15)
            ct = self.d(className="android.widget.ImageView").count
            print ct
            for i in xrange(0, ct):
                b = self.d(className="android.widget.ImageView")[i].bounds
                box = (b["left"] + 10, b["top"] + 10, int(b["right"]-10), int(b["bottom"] -10))
                self.miniscreenShot()
                img = Image.open("ctstmp.png")
                img_0 = img.crop(box)
                color = GetMainColor.get_dominant_color(img_0)
                get = GetMainColor.min_color_diff(color)
                print get
                if len(get) == 2:
                    if get[1] == "RED" or get[1] == "ORANGE":
                        result = False
                        print get[1]
            print result
            if result:
                self.press_pass()
            else:
                self.press_pass(tof=False)
        except Exception,e:
            import traceback
            traceback.print_exc()

    def test_BatterySaving(self):
        self.d.watchers.run()
        print "test_BatterySaving"
        self.startapp("com.android.settings", "com.android.settings.Settings")
        self.gototext(COME_TO[SETTINGS]["Location"])
        if self.d(text="Off").exists:
            self.d(text="Off").click()
            time.sleep(1)
            self.d.press.back()
            self.d.press.back()
            self.d.press.back()
        self.startapp("com.android.cts.verifier", "com.android.cts.verifier.CtsVerifierActivity")
        time.sleep(2)
        local = ["Battery Saving Mode Test", "Device Only Mode Test", "High accuracy"]
        for i in local:
            if not (self.findtext(i)):
                time.sleep(1)
                print "no ", i, " Mode found!"
                return 0
            time.sleep(5)
            en = self.d(textStartsWith="Please select").down(text="LAUNCH SETTINGS").enabled
            if en:
                self.d(textStartsWith="Please select").down(text="LAUNCH SETTINGS").click()
                time.sleep(1)

                if self.d(text="Off").exists:
                        self.d(text="Off").click()
                        time.sleep(1)

                self.d(text="Mode").click()
                self.d(textStartsWith=i.split()[0]).click()
                time.sleep(1)
                self.d.press.back()
                self.d.press.back()
                time.sleep(3)
            self.press_pass()

    def test_LocationOff(self):
        if not (self.findtext("Location Mode Off Test")):
            print "no Location Mode Off Test Mode found!"
            return 0
        time.sleep(1)
        if self.d(text="LAUNCH SETTINGS").enabled:
            self.d(text="LAUNCH SETTINGS").click()
            time.sleep(1)
            if self.d(text="ON").exists:
                self.d(text="ON").click()
                if self.d(text="TURN ON LOCATION").exists:
                    self.d(text="CLOSE").click()
                    time.sleep(1)
                self.d.press.back()
                time.sleep(2)
        self.press_pass()

    def test_BYODManaged(self):
        self.watch()
        # print "test_BYODManaged"
        # if not (self.findtext("BYOD Managed Provisioning")):
        #     print "no BYOD Managed Provisioning found!"
        #     return 0
        # time.sleep(1)
        # self.d(text="START BYOD PROVISIONING FLOW").click()
        # if self.d(text="DELETE").exists:
        #     self.d(text="DELETE").click()
        #     time.sleep(5)
        #     self.d(text="START BYOD PROVISIONING FLOW").click()
        #     time.sleep(1)
        # if self.d(text="ACCEPT & CONTINUE").exists:
        #     self.d(text="ACCEPT & CONTINUE").click()
        #     time.sleep(15)
        if tkinter.messagebox.askokcancel('提示', '请确定已经加密!'):
        #     self.d(text="Full disk encryption enabled").click()
        #     time.sleep(1)
        #     if self.d(text="GO").exists:
        #         self.d(text="GO").click()
        #         time.sleep(1)
        #     if self.d(text="Re-enter your password").exists:
        #         self.raw_cmd('shell', 'input', 'text', '1111')
        #         time.sleep(1)
        #         self.raw_cmd('shell', 'input', 'keyevent', '66')
        #         time.sleep(1)
        #     if self.d(text="Continue without fingerprint").exists:
        #         self.d(text="Continue without fingerprint").click()
        #         time.sleep(1)
        #
        #     if self.d(text="PIN").exists:
        #         self.d(text="PIN").click()
        #         time.sleep(1)
        #         self.d(text="YES").click()
        #         time.sleep(1)
        #         if self.d(text="OK").exists:
        #             self.d(text="OK").click()
        #         if self.d(text="Require PIN?").exists:
        #             self.d(text="OK").click()
        #             time.sleep(2)
        #         self.raw_cmd('shell', 'input', 'text', '1111')
        #         time.sleep(1)
        #         self.d(text="NEXT").click()
        #         time.sleep(1)
        #         self.raw_cmd('shell', 'input', 'text', '1111')
        #         time.sleep(1)
        #         self.d(text="OK").click()
        #         time.sleep(5)
        #         if self.d(text="DONE").exists:
        #             self.d(text="DONE").click()
        #             time.sleep(5)
        #     if self.d(text="GO").exists:
        #         self.d(text="GO").click()
        #         time.sleep(2)
        #         if self.d(text="Re-enter your PIN").exists:
        #             self.raw_cmd('shell', 'input', 'text', '1111')
        #             time.sleep(1)
        #             self.raw_cmd('shell', 'input', 'keyevent', '66')
        #             time.sleep(2)
        #             if self.d(text="Continue without fingerprint").exists:
        #                 self.d(text="Continue without fingerprint").click()
        #             if self.d(text="None").exists:
        #                 self.d(text="None").click()
        #                 time.sleep(0.5)
        #                 self.d(textContains="YES").click()
        #                 time.sleep(2)
        #     if self.d(text="PASS").exists:
        #         self.d(text="PASS").click()
        #         time.sleep(2)
        #
        #     self.d(text="Badged work apps visible in Launcher").click()
        #     self.d(text="GO").click()
        #     time.sleep(1)
        #     self.d.swipe(500, 700, 500, 50, steps=10)
        #     time.sleep(1)
        #     getORno = self.find_template("verify_work_icon_x600.1080x2246.png")
        #     time.sleep(1)
        #     self.back2Verify()
        #     if getORno!=None:
        #         self.d(text="PASS").click()
        #         time.sleep(1)
        #     else:
        #         self.d(text="FAIL").click()
        #         time.sleep(1)
        #     # test 3
        #     self.d(text="Work notification is badged").click()
        #     self.d(text="GO").click()
        #     time.sleep(2)
        #     self.d.open.notification()
        #     time.sleep(0.5)
        #     time.sleep(2)
        #
        #     getORno2 = self.find_template("work.png")
        #     time.sleep(1)
        #     self.d.press.back()
        #     if getORno2!=None:
        #         self.d(text="PASS").click()
        #         time.sleep(1)
        #     else:
        #         self.d(text="FAIL").click()
        #         time.sleep(1)
        #
        #
        #     self.d(text="Work status icon is displayed").click()
        #     self.d(text="GO").click()
        #     time.sleep(2)
        #
        #     getORno3 = self.find_template("status.png")
        #     time.sleep(1)
        #     self.d(text="FINISH").click()
        #     if getORno3[0] != None:
        #         self.d(text="PASS").click()
        #         time.sleep(1)
        #     else:
        #         self.d(text="FAIL").click()
        #         time.sleep(1)
        #
        #
        #     self.findtext("Work status toast is displayed")
        #     self.d(text="GO").click()
        #     time.sleep(1)
        #     self.d.sleep()
        #     time.sleep(6)
        #     self.d.wakeup()
        #     self.d.swipe(400, 800, 400, 100, steps=20)
        #     time.sleep(2)
        #     if self.d(resourceId="com.android.systemui:id/pinEntry").exists:
        #         self.raw_cmd('shell', 'input', 'text', '1111')
        #         time.sleep(0.5)
        #         self.raw_cmd('shell', 'input', 'keyevent', '66')
        #     getORno4 = self.find_template("tost_x600.png")
        #     time.sleep(1)
        #     self.d(text="FINISH").click()
        #     if getORno4!=None:
        #             self.d(text="PASS").click()
        #             time.sleep(1)
        #     else:
        #             self.d(text="FAIL").click()
        #             time.sleep(1)
        #
        #
        #     self.findtext("Profile-aware accounts settings")
        #     self.d(text="GO").click()
        #     time.sleep(1)
        #     self.findtext("Users & accounts")
        #     result = self.d(text="Personal").exists & self.d(text="Work").exists
        #     self.back2Verify()
        #     if result:
        #         self.d(text="PASS").click()
        #         time.sleep(1)
        #     else:
        #         self.d(text="FAIL").click()
        #         time.sleep(1)
        #
        #
        #     self.findtext("Profile-aware device administrator settings")
        #     self.d(text="GO").click()
        #     time.sleep(1)
        #     self.findtext("Device admin apps")
        #     time.sleep(1)
        #     getORno = self.find_template("DeviceAdminApp_VBbag1.720x1440.png")
        #     self.d.click(int(getORno[0]), int(getORno[1]))
        #     result = self.find_template("remove_work_profile_x600.1080x2246.png")!=None
        #     self.d.press.back()
        #     self.d.press.back()
        #     self.d.press.back()
        #
        #     if result:
        #         self.d(text="PASS").click()
        #         time.sleep(1)
        #     else:
        #         self.d(text="FAIL").click()
        #         time.sleep(1)
        #
        #
        #     self.findtext("Profile-aware trusted credential settings")
        #     self.d(text="GO").click()
        #     time.sleep(1)
        #     self.findtext("Encryption & credentials")
        #     time.sleep(1)
        #     self.findtext("Trusted credentials")
        #     time.sleep(15)
        #
        #     result = self.d(text="Personal").exists & self.d(text="Work").exists
        #     self.d.press.back()
        #     self.d.press.back()
        #     self.d.press.back()
        #     if result:
        #         self.d(text="PASS").click()
        #         time.sleep(1)
        #     else:
        #         self.d(text="FAIL").click()
        #         time.sleep(1)
        #
        #     # test 9
        #     self.findtext("Profile-aware app settings")
        #     self.d(text="GO").click()
        #     time.sleep(2)
        #     self.d(text="All apps").click()
        #     time.sleep(2)
        #     result = (self.d(text="Personal").exists) & (self.d(text="Work").exists)
        #     self.d.press.back()
        #     time.sleep(1)
        #     self.d.press.back()
        #     time.sleep(1)
        #     if result:
        #         self.d(text="PASS").click()
        #         time.sleep(1)
        #     else:
        #         self.d(text="FAIL").click()
        #         time.sleep(1)
        #
        #
        #     self.findtext("Profile-aware location settings")
        #     self.d(text="GO").click()
        #     time.sleep(2)
        #     result =True
        #     if self.d(text="On").exists:
        #         result = self.d(text="Location for work profile").right(className="android.widget.Switch").checked
        #         self.d(text="On").click()
        #         time.sleep(1)
        #         result = result & (self.d(text="Off").exists)
        #         result = result & (not self.d(text="Location for work profile").right(className="android.widget.Switch").checked)
        #         time.sleep(1)
        #         self.d(text="Off").click()
        #         time.sleep(1)
        #         result = result & self.d(text="On").exists
        #         result = result & (self.d(text="Location for work profile").right(className="android.widget.Switch").checked)
        #
        #     self.d.press.back()
        #     if result:
        #         self.d(text="PASS").click()
        #         time.sleep(1)
        #     else:
        #         self.d(text="FAIL").click()
        #         time.sleep(1)
        #
        #     self.findtext("Profile-aware printing settings")
        #     self.d(text="GO").click()
        #     time.sleep(1)
        #     result = self.d(text="Personal").exists
        #     if result:
        #         self.d(text="Personal").click()
        #         time.sleep(1)
        #         result = result & self.d(text="Work").exists
        #         self.d.press.back()
        #     self.d.press.back()
        #     if result:
        #         self.d(text="PASS").click()
        #         time.sleep(1)
        #     else:
        #         self.d(text="FAIL").click()
        #         time.sleep(1)
        #
        #
        #     self.findtext("Open app cross profiles from the personal side")
        #     self.d(text="GO").click()
        #     time.sleep(1)
        #     result = (("SWITCH TO WORK") in self.d.dump()) & ("CTS Verifier" in self.d.dump())
        #     self.d.press.back()
        #     time.sleep(1)
        #     if result:
        #         self.d(text="PASS").click()
        #     else:
        #         self.d(text="FAIL").click()
        #     time.sleep(1)
        #
        #
        #     self.findtext("Open app cross profiles from the work side")
        #     self.d(text="GO").click()
        #     time.sleep(1)
        #     result = self.find_template("verify_icon_white.1080x2246.png")!=None
        #     self.d.press.back()
        #     if result:
        #         self.d(text="PASS").click()
        #         time.sleep(1)
        #     else:
        #         self.d(text="FAIL").click()
        #         time.sleep(1)
        #     os.system(
        #         'adb -s ' + self.serial + ' install -r ' + os.getcwd() + '/android-cts-verifier_8.1/CtsPermissionApp.apk')
        #
        #     self.findtext("Disable non-market apps")
        #     self.d(text="GO").click()
        #     time.sleep(3)
        #     xml = self.d.dump()
        #     result = "Action not allowed" in xml
        #     if result:
        #         time.sleep(1)
        #         result = result & ("packageinstaller" not in self.getPackage()[0])
        #         self.d.press.back()
        #     if result:
        #         self.d(text="PASS").click()
        #         time.sleep(1)
        #     else:
        #         self.d(text="FAIL").click()
        #         time.sleep(1)
        #
        #     self.findtext("Enable non-market apps")
        #     self.d(text="GO").click()
        #     time.sleep(3)
        #     if self.d(text="SETTINGS").exists:
        #         self.d(text="SETTINGS").click()
        #         self.d(text="Allow from this source").click()
        #         time.sleep(1)
        #         self.d.press.back()
        #         time.sleep(2)
        #     result = self.d(text="INSTALL").exists
        #     if result:
        #         result = result & ("packageinstaller" in self.getPackage()[0])
        #         self.d(text="INSTALL").click()
        #         time.sleep(2)
        #         result = result & (self.d(text="PASS").exists)
        #     if result:
        #         self.d(text="PASS").click()
        #     else:
        #         self.d(text="FAIL").click()
        #     time.sleep(1)
        #
        #
        #     self.findtext("Cross profile intent filters are set")
        #     time.sleep(5)
        #     os.system(
        #             'adb -s ' + self.serial + ' install -r ' + os.getcwd() + '/android-cts-verifier_8.1/CtsPermissionApp.apk')
        #
        #     self.findtext("Permissions lockdown")
        #
        #     self.d(text="GO").click()
        #     time.sleep(2)
        #     if self.d(text="Grant").exists:
        #         self.d(text="Grant",className="android.widget.RadioButton").click()
        #         self.clicktext(text= "OPEN APPLICATION SETTINGS")
        #         time.sleep(2)
        #         self.clicktext(text= "Permissions")
        #         time.sleep(2)
        #         result1 = not self.d(text="Contacts").enabled
        #         time.sleep(1)
        #         self.d(text="Contacts").click()
        #         time.sleep(1)
        #         result1 = result1 & ("Action not allowed" in self.d.dump())
        #         if result1:
        #             time.sleep(1)
        #             result1 = result1 & ("More details" in self.d.dump())
        #             self.d.press.back()
        #             self.d.press.back()
        #             self.d.press.back()
        #         #
        #         self.d(text="Let user decide", className="android.widget.RadioButton").click()
        #         self.d(text="OPEN APPLICATION SETTINGS").click()
        #         time.sleep(2)
        #         self.d(text="Permissions").click()
        #         time.sleep(1)
        #         result2 = self.d(text="Contacts").enabled
        #         time.sleep(1)
        #         result2 = result2 & self.d(resourceId="android:id/switch_widget").enabled
        #         self.d.press.back()
        #         self.d.press.back()
        #         #
        #         self.d(text="Deny", className="android.widget.RadioButton").click()
        #         self.d(text="OPEN APPLICATION SETTINGS").click()
        #         time.sleep(2)
        #         self.d(text="Permissions").click()
        #         time.sleep(1)
        #         result3 = not self.d(text="Contacts").enabled
        #         time.sleep(1)
        #         self.d(text="Contacts").click()
        #         time.sleep(1)
        #         result3 = result3 & ("Action not allowed" in self.d.dump())
        #         if result3:
        #             time.sleep(1)
        #             result3 = result3 & ("More details" in self.d.dump())
        #             self.d.press.back()
        #             self.d.press.back()
        #             self.d.press.back()
        #         self.d(text="FINISH").click()
        #         if result1 & result2 & result3:
        #             self.d(text="PASS").click()
        #             time.sleep(1)
        #         else:
        #             self.d(text="FAIL").click()
        #             time.sleep(1)
        #     else:
        #         self.d(text="FAIL").click()
        #     self.findtext("Keyguard disabled features")
        #     time.sleep(1)
        #     self.startapp("com.android.settings","com.android.settings.Settings")
        #     time.sleep(1)
        #     self.gototext(COME_TO[SETTINGS]["administrators"])
        #     time.sleep(1)
        #     ct = self.d(text="CTS Verifier").count
        #
        #     for i in xrange(0, ct):
        #         if not self.d(text="CTS Verifier")[i].right(resourceId="com.android.settings:id/checkbox").checked:
        #             self.d(text="CTS Verifier")[i].right(resourceId="com.android.settings:id/checkbox").click()
        #             time.sleep(1)
        #             if not self.findtext("Activate this device"):
        #                 self.d.press.back()
        #         time.sleep(1)
        #
        #     self.d.press.back()
        #     self.d.press.back()
        #     self.setpassword("Password", "1111")
        #     self.d.press.back()
        #     time.sleep(1)
        #     self.back2Verify()
        #     self.d(text="PREPARE TEST").click()
        #     time.sleep(1)
        #     self.d(text="Disable trust agents").click()
        #     self.d(text="GO").click()
        #     self.findtext("Trust agents")
        #
        #     ass3_result = False
        #     if not self.d(resourceId="android:id/title").enabled:
        #         ass3_result = (self.find_template("trustagents.720x1440.png") != None)
        #         self.d.press.back()
        #         time.sleep(2)
        #     self.d.press.back()
        #     self.d.press.back()
        #     if ass3_result:
        #         self.d(text="PASS").click()
        #         time.sleep(1)
        #     else:
        #         self.d(text="FAIL").click()
        #         time.sleep(1)
        #     self.d(text="Unredacted notifications disabled on keyguard").click()
        #     time.sleep(1)
        #     self.d(text="GO").click()
        #     time.sleep(5)
        #     self.d.wakeup()
        #     result = self.d(text="Contents hidden by policy").exists
        #     self.d.swipe(500, 700, 500, 100, steps=10)
        #     time.sleep(1)
        #     self.isLocked()
        #     self.back2Verify()
        #     if result:
        #         self.d(text="PASS").click()
        #     else:
        #         self.d(text="FAIL").click()
        #     time.sleep(1)
        #
        #     self.d(text="Fingerprint is disabled in Settings").click()
        #     time.sleep(1)
        #     self.d(text="GO").click()
        #     time.sleep(2)
        #     self.d(text="Fingerprint").click()
        #     time.sleep(2)
        #     notetext = self.d.dump()
        #     time.sleep(1)
        #     self.d.press.back()
        #     time.sleep(1)
        #     self.d.press.back()
        #     time.sleep(2)
        #
        #     result = "t use your fingerprint" in notetext
        #
        #     if result:
        #         self.d(text="PASS").click()
        #     else:
        #         self.d(text="FAIL").click()
        #     time.sleep(2)
        #     self.d(text="Fingerprint disabled on keyguard").click()
        #     time.sleep(1)
        #     self.d(text="PASS").click()
        #     self.press_pass()
        #     #test 17
        #
        #     self.findtext("Authentication-bound keys")
        #     if self.d(text="OK").exists:
        #         self.d(text="OK").click()
        #     self.d(text="SET UP").click()
        #     if tkinter.messagebox.askokcancel('提示', '请在work profile设置密码和指纹,然后返回'):
        #         self.back2Main()
        #         self.d(text="Lockscreen-bound key test").click()
        #     time.sleep(5)
        #     if self.d(textStartsWith="Re-enter").exists:
        #         self.raw_cmd('shell', 'input', 'text', '1111')
        #         time.sleep(0.5)
        #         self.raw_cmd('shell', 'input', 'keyevent', '66')
        #     time.sleep(2)
        #     self.d(text="Fingerprint-bound key test").click()
        #     if tkinter.messagebox.askokcancel('提示', '请指纹放在解锁上'):
        #             self.press_pass()
        #
        #     self.findtext("VPN test")
        #     self.press_pass()

            self.findtext("Always-on VPN Settings")
            cmds = ('adb -s ' + self.serial +  ' uninstall com.android.cts.vpnfirewall')
            os.system(cmds)
            cmds = ('adb -s '+ self.serial+ ' install -r ' +os.getcwd() + "/android-cts-verifier_8.1/CtsVpnFirewallAppApi23.apk")
            os.system(cmds)

            time.sleep(1)
            self.d(text="PREPARE VPN").click()
            time.sleep(1)
            self.d(text="VPN app targeting SDK 23").click()

            self.d(text="GO").click()
            time.sleep(1)
            self.d(resourceId="com.android.settings:id/settings_button").click()
            result = not self.d(text="Always-on VPN").enabled
            result = result & (not self.d(text="Block connections without VPN").enabled)
            result = result & (not self.d(text="Always-on VPN").right(resourceId="android:id/switch_widget").checked)
            result = result & (
            not self.d(text="Block connections without VPN").right(resourceId="android:id/switch_widget").checked)
            self.d.press.back()
            self.d.press.back()
            if result:
                self.d(text="PASS").click()
                time.sleep(1)
            else:
                self.d(text="FAIL").click()
                time.sleep(1)

            self.d(text="VPN app targeting SDK 24").click()

            cmds = ('adb -s ' + self.serial + ' install -r ' + os.getcwd() + "/android-cts-verifier_8.1/CtsVpnFirewallAppApi24.apk")
            os.system(cmds)

            time.sleep(1)
            self.d(text="GO").click()
            time.sleep(1)
            self.d(resourceId="com.android.settings:id/settings_button").click()
            result = self.d(text="Always-on VPN").enabled
            result = result & (not self.d(text="Block connections without VPN").enabled)
            result = result & (not self.d(text="Always-on VPN").right(resourceId="android:id/switch_widget").checked)
            result = result & (not self.d(text="Block connections without VPN").right(
                resourceId="android:id/switch_widget").checked)
            self.d.press.back()
            self.d.press.back()
            if result:
                self.d(text="PASS").click()
                time.sleep(1)
            else:
                self.d(text="FAIL").click()
                time.sleep(1)

            self.d(text="VPN app with opt-out").click()
            cmds = ['adb', '-s', self.serial, 'install', '-r -t',
                    os.getcwd() + r"/android-cts-verifier_8.1/CtsVpnFirewallAppNotAlwaysOn.apk"]
            subprocess.Popen(cmds, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()[0]
            self.d(text="GO").click()
            time.sleep(2)
            self.d(resourceId="com.android.settings:id/settings_button").click()
            result = not self.d(text="Always-on VPN").enabled
            result = result & (not self.d(text="Block connections without VPN").enabled)
            result = result & (not self.d(text="Always-on VPN").right(resourceId="android:id/switch_widget").checked)
            result = result & (
                not self.d(text="Block connections without VPN").right(resourceId="android:id/switch_widget").checked)
            self.d.press.back()
            self.d.press.back()
            if result:
                self.d(text="PASS").click()
                time.sleep(1)
            else:
                self.d(text="FAIL").click()
                time.sleep(1)
            self.press_pass()
            #
            # self.removepassword()
            # self.back2Verify()

            # self.findtext("Turn off work mode")
            # self.d(text="Prepare a work notification").click()
            # self.d(text="GO").click()
            # time.sleep(1)
            # self.d.open.notification()
            # time.sleep(0.5)
            # ass5_result = self.d(text="This is a notification").exists
            # time.sleep(0.5)
            # self.d.press.back()
            # if ass5_result:
            #     self.d(text="PASS").click()
            # else:
            #     self.d(text="FAIL").click()
            # time.sleep(1)
            #
            # self.d(text="OPEN SETTINGS TO TOGGLE WORK MODE").click()
            # self.d(text="Work profile settings").click()
            # time.sleep(1)
            # if self.d(resourceId="android:id/switch_widget").checked:
            #     self.d(resourceId="android:id/switch_widget").click()
            # self.d.press.back()
            # self.d.press.back()
            # self.d(text="Please turn off work mode").click()
            # time.sleep(2)
            #
            # self.d(text="Notifications when work mode is off").click()
            # time.sleep(1)
            # self.d.open.notification()
            # result = not self.d(text="This is a notification").exists
            # self.d.press.back()
            # time.sleep(1)
            # if result:
            #     self.d(text="PASS").click()
            # else:
            #     self.d(text="FAIL").click()
            # time.sleep(1)
            #
            # self.d(text="Status bar icon when work mode is off").click()
            # getORno3 = self.find_template("status_off.png")
            # time.sleep(1)
            # if getORno3[0]!=None:
            #     self.d(text="PASS").click()
            #     time.sleep(1)
            # else:
            #     self.d(text="FAIL").click()
            #     time.sleep(1)
            #
            # self.findtext("Starting work apps when work mode is off")
            # time.sleep(1)
            # self.d.press.home()
            # time.sleep(2)
            # self.d.swipe(400, 800, 400, 100, steps=20)
            # time.sleep(1)
            # getORno4 = self.find_template("work_off_x600.1080x2246.png")
            # if getORno4[0]!=None:
            #     self.d.click(int(getORno4[0]), int(getORno4[1]))
            #     time.sleep(1)
            # result = self.d(text="Turn on work mode?").exists
            # time.sleep(1)
            # self.d.press.back()
            # self.d.press.back()
            # self.back2Verify()
            # if result:
            #     self.d(text="PASS").click()
            # else:
            #     self.d(text="FAIL").click()
            # time.sleep(1)
            #
            # self.d(text="OPEN SETTINGS TO TOGGLE WORK MODE").click()
            # self.d(text="Work profile settings").click()
            # time.sleep(1)
            # if not self.d(resourceId="android:id/switch_widget").checked:
            #     self.d(resourceId="android:id/switch_widget").click()
            #     time.sleep(1)
            #     if self.d(text="Re-enter your password").exists:
            #         self.raw_cmd('shell', 'input', 'text', '1111')
            #         time.sleep(0.5)
            #         self.raw_cmd('shell', 'input', 'keyevent', '66')
            #         time.sleep(2)
            #     else:
            #         if self.d(textStartsWith="Re-enter your").exists:
            #             self.raw_cmd('shell', 'input', 'text', '1111')
            #             time.sleep(0.5)
            #             self.raw_cmd('shell', 'input', 'keyevent', '66')
            #             time.sleep(2)
            # self.d.press.back()
            # self.d.press.back()
            # self.findtext("Please turn work mode back on")
            # time.sleep(5)
            #
            # getORno3 = self.find_template("status_off.png")
            # self.d(text="Status bar icon when work mode is on").click()
            # if getORno3!=None:
            #     self.d(text="PASS").click()
            #     time.sleep(1)
            # else:
            #     self.d(text="FAIL").click()
            #     time.sleep(1)
            #
            # self.findtext("Starting work apps when work mode is on")
            # time.sleep(1)
            # self.d.press.home()
            # time.sleep(2)
            # self.d.swipe(400, 800, 400, 100, steps=20)
            # time.sleep(1)
            # self.d(text="CTS Verifier")[1].click()
            # result = self.d(text="ALLOW").exists
            # time.sleep(1)
            # self.back2Verify()
            # if result:
            #     self.d(text="PASS").click()
            # else:
            #     self.d(text="FAIL").click()
            # time.sleep(1)
            # self.press_pass()
            #
            # self.findtext("Select work lock test")
            # time.sleep(1)
            # self.d(text="GO").click()
            # time.sleep(1)
            # if self.d(text="Choose work lock").exists:
            #     result =self.d(text="PIN").exists
            #     if result:
            #         self.d(text="PIN").click()
            #         self.raw_cmd('shell', 'input', 'text', '1111')
            #         time.sleep(1)
            #         self.raw_cmd('shell', 'input', 'keyevent', '66')
            #         time.sleep(1)
            #         self.raw_cmd('shell', 'input', 'text', '1111')
            #         time.sleep(1)
            #         self.raw_cmd('shell', 'input', 'keyevent', '66')
            #         time.sleep(1)
            #         if self.d(text="DONE").exists:
            #             self.d(text="DONE").click()
            # else:
            #     result = self.d(text="Unlock selection").exists
            #     if result:
            #         self.clicktext(method="textStartsWith",text="Fingerprint + PIN")
            #         self.raw_cmd('shell', 'input', 'text', '1111')
            #         time.sleep(1)
            #         self.raw_cmd('shell', 'input', 'keyevent', '66')
            #         time.sleep(1)
            #         self.raw_cmd('shell', 'input', 'text', '1111')
            #         time.sleep(1)
            #         self.raw_cmd('shell', 'input', 'keyevent', '66')
            #         time.sleep(1)
            # if result:
            #     self.d(text="PASS").click()
            # else:
            #     self.d(text="FAIL").click()
            # time.sleep(1)

            self.findtext("Confirm work lock test")
            time.sleep(1)
            self.d(text="GO").click()
            time.sleep(2)
            self.d.swipe(400, 800, 400, 100, steps=20)
            time.sleep(2)
            self.d(text="CTS Verifier")[1].click()

            time.sleep(2)
            result = self.d(text="CtsVerifier").exists
            result = result & self.d(text="CANCEL").exists

            box = (int(self.wmsize[0]) / 2,int(self.wmsize[1]) / 2,int(self.wmsize[0]) / 2 +50,int(self.wmsize[1]) / 2 +50)
            self.miniscreenShot()
            img_0 = Image.open("ctstmp.png")
            img_0 = img_0.crop(box)
            color = GetMainColor.get_dominant_color(img_0)
            get = GetMainColor.min_color_diff(color)
            print get
            self.d.press.back()
            self.d.press.back()
            self.back2Verify()
            if "BLUE" ==get[1]:
                self.d(text="PASS").click()
            else:
                self.d(text="FAIL").click()
            time.sleep(1)


    def test_BYOD_Provisioning(self):
        print "BYOD Provisioning tests"
        if not (self.findtext("BYOD Provisioning tests")):
            print "BYOD Provisioning tests not found!"
            return 0
        time.sleep(2)
        self.d(text="Custom provisioning color").click()
        self.d(text="GO").click()
        if self.d(text="DELETE").exists:
            self.d(text="DELETE").click()

        box = (int(self.wmsize[0])/2-10, 1, int(self.wmsize[0])/2+10, 10)
        self.miniscreenShot()
        img = Image.open("ctstmp.png")
        img_0 = img.crop(box)
        b = self.d(text="ACCEPT & CONTINUE").bounds
        box1 =  (b["left"], b["top"], b["right"], b["bottom"])

        img_1 = img.crop(box1)
        color = GetMainColor.get_dominant_color(img_0)

        get = GetMainColor.min_color_diff(color)
        color1 = GetMainColor.get_dominant_color(img_1)
        get1 = GetMainColor.min_color_diff(color1)
        print get,get1
        self.back2Main()
        if "GREEN" ==get[1] and "GREEN" ==get1[1]:
                self.press_pass()
                result = True
        else:
                self.press_pass(tof=False)
                result =False
        time.sleep(1)

        self.d(text="Custom provisioning image").click()
        self.d(text="GO").click()
        if self.d(text="DELETE").exists:
            self.d(text="DELETE").click()
        self.d(text="ACCEPT & CONTINUE").click()
        fi = self.find_template("verify_icon.720x1440.png")
        if fi!=None:
                self.press_pass()
        else:
                self.press_pass(tof=False)
                result = False
        time.sleep(2)

        self.d(text="Custom terms").click()
        self.d(text="GO").click()
        if self.d(text="DELETE").exists:
            self.d(text="DELETE").click()
        self.d(text="View terms").click()
        self.d(text="Company ABC").click()
        time.sleep(1)
        fi = self.d(textStartsWith="Company Terms Content").exists
        self.d.press.back()
        self.d.press.back()
        if fi!=None:
                self.press_pass()
        else:
                self.press_pass(tof=False)
                result = False
        time.sleep(1)
        self.press_pass(tof=result)

    def test_DeviceOwner(self):
        try:
            self.watch()
            # print "Device Owner Requesting Bugreport Tests"
            # if not (self.findtext("Device Owner Requesting Bugreport Tests")):
            #     print "Device Owner Requesting Bugreport Tests not found!"
            #     return 0
            # os.system("adb -s "+ self.serial +" shell dpm set-device-owner 'com.android.cts.verifier/com.android.cts.verifier.managedprovisioning.DeviceAdminTestReceiver'")
            # time.sleep(4)
            # self.d(text="SET UP DEVICE OWNER").click()
            time.sleep(4)
            self.d(text="Check device owner").click()
            time.sleep(2)
            self.d(text="Sharing of requested bugreport declined while being taken").click()
            time.sleep(1)
            self.clear_notification()
            self.d(text="REQUEST BUGREPORT").click()
            time.sleep(1)
            self.d.open.notification()
            ass1 = self.d(textStartsWith="Taking bug report").wait.exists(timeout=1000)
            self.d.press.back()
            self.d(text="REQUEST BUGREPORT").click()
            self.d.open.notification()
            ass1 = ass1 & self.d(textStartsWith="Device Owner Requesting Bugreport").wait.exists(timeout=1000)
            ass1 = ass1 & self.d(textStartsWith="Bugreport is already being collected").exists
            self.d(textStartsWith="Taking bug report").click()
            time.sleep(1)
            ass1 = ass1 & self.d(textStartsWith="Your IT admin").exists
            ass1 = ass1 & self.d(text="DECLINE").exists & self.d(text="SHARE").exists
            self.d(text="DECLINE").click()
            time.sleep(0.5)
            self.d.open.notification()
            ass1 = ass1 &  self.d(textStartsWith="Taking bug report").wait.gone(timeout=1000)
            ass1 = ass1 & self.d(text="Bugreport Sharing declined").wait.gone(timeout=1000)
            self.d.press.back()
            time.sleep(1)
            if ass1:
                self.press_pass()
            else:
                self.press_pass(tof=False)
            self.clear_notification()

            self.d(text="Sharing of requested bugreport accepted while being taken").click()
            self.d(text="REQUEST BUGREPORT").click()
            time.sleep(1)
            self.d.open.notification()
            ass1 = self.d(textStartsWith="Taking bug report").wait.exists(timeout=2000)
            time.sleep(1)
            self.d(textStartsWith="Taking bug report").click()
            time.sleep(1)
            ass1 = ass1 & self.d(textStartsWith="Share bug report").exists
            ass1 = ass1 & self.d(text="DECLINE").exists & self.d(text="SHARE").exists
            self.d(text="SHARE").click()
            self.d.open.notification()
            ass1 = ass1 & self.d(textStartsWith="Taking bug report").wait.gone(timeout=1000)
            ass1 = ass1 & self.d(textStartsWith="Sharing bug report").wait.gone(timeout=120000)
            ass1 = ass1 & self.d(text="Bugreport shared successfully").wait.exists(timeout=20000)
            self.d.press.back()
            time.sleep(2)
            if ass1:
                self.press_pass()
            else:
                self.press_pass(tof=False)

            self.clear_notification()
            self.d(text="Sharing of requested bugreport declined after having been taken").click()
            self.d(text="REQUEST BUGREPORT").click()
            time.sleep(1)
            self.d.open.notification()
            time.sleep(1)
            ass1 = self.d(textStartsWith="Taking bug report").wait.gone(timeout=120000)
            ass1 = ass1 & self.d(textStartsWith="Share bug report").wait.exists(timeout=20000)
            ass1 = ass1 & self.d(text="DECLINE").exists & self.d(text="SHARE").exists
            time.sleep(1)
            self.d(text="DECLINE").click()
            time.sleep(1)
            ass1 = ass1 & self.d(text="Bugreport sharing declined").wait.exists(timeout=1000)
            self.d.press.back()
            time.sleep(2)
            if ass1:
                self.press_pass()
            else:
                self.press_pass(tof=False)

            self.clear_notification()
            self.d(text="Sharing of requested bugreport accepted after having been taken").click()
            self.d(text="REQUEST BUGREPORT").click()
            time.sleep(1)
            self.d.open.notification()
            time.sleep(1)
            ass1 = self.d(textStartsWith="Taking bug report").wait.gone(timeout=120000)
            ass1 = ass1 & self.d(textStartsWith="Share bug report").wait.exists(timeout=20000)
            ass1 = ass1 & self.d(text="DECLINE").exists & self.d(text="SHARE").exists
            self.d(text="SHARE").click()
            time.sleep(1)
            ass1 = ass1 & self.d(text="Bugreport shared successfully").wait.exists(timeout=1000)
            self.d.press.back()
            time.sleep(2)
            if ass1:
                self.press_pass()
            else:
                self.press_pass(tof=False)
            self.clear_notification()
        finally:
            self.startapp("com.android.settings", "com.android.settings.Settings")
            time.sleep(1)
            self.gototext(COME_TO[SETTINGS]["administrators"])
            result = self.d(text="CTS Verifier").right(resourceId="com.android.settings:id/checkbox").checked
            self.back2Verify()
            self.d(text="Remove device owner").click()
            self.d(text="REMOVE DEVICE OWNER").click()
            time.sleep(2)
            self.startapp("com.android.settings", "com.android.settings.Settings")
            time.sleep(1)
            self.gototext(COME_TO[SETTINGS]["administrators"])
            ct = self.d(text="CTS Verifier").count
            result1 = True
            for i in xrange(0, ct):
                result1 = result1 & (not self.d(text="CTS Verifier")[i].right(resourceId="com.android.settings:id/checkbox").checked)
                time.sleep(1)
            self.back2Verify()
            time.sleep(1)
            if result1 and result:
                self.press_pass()
            else:
                self.press_pass(tof=False)
            self.press_pass()

    def test_DeviceOwneTest(self):
        try:
            # os.system('adb -s '+self.serial + ' install -r -t '+ os.getcwd() + "/android-cts-verifier_8.1/CtsEmptyDeviceOwner.apk")
            #
            # if self.d(text="ACCEPT").exists:
            #     self.d(text="ACCEPT").click()
            # time.sleep(3)
            # os.system(
            #     "adb -s " + self.serial + " shell dpm set-device-owner com.android.cts.emptydeviceowner/.EmptyDeviceAdmin")
            #
            # print "test_DeviceOwneTest"
            # if not (self.findtext("Device Owner Tests")):
            #     print "Device Owner Test not found!"
            #     return 0
            # if self.d(text="PRECONDITION CHECKS").exists:
            #     self.d(text="PRECONDITION CHECKS").click()
            #     time.sleep(1)
            #
            # if self.d(text="Precondition checks").exists:
            #     self.d(text="OK").click()
            #     time.sleep(1)
            # if self.d(text="OK").exists:
            #     self.d(text="OK").click()
            #     time.sleep(1)
            # os.system(
            #         "adb -s " + self.serial + " shell dpm set-device-owner 'com.android.cts.verifier/com.android.cts.verifier.managedprovisioning.DeviceAdminTestReceiver'")
            # time.sleep(3)


            # self.clicktext(text="Check device owner")
            # time.sleep(2)
            # self.watch()
            # self.clicktext(text="Device administrator settings")
            # self.clicktext(text="GO")
            # self.findtext("Device admin apps")
            # result =self.d(text="CTS Verifier").right(resourceId="com.android.settings:id/checkbox").checked
            # self.d(text="CTS Verifier").click()
            # result =result & (not self.d(text="Deactivate this device admin app").enabled)
            # self.d.press.back()
            # self.d.press.back()
            # self.d.press.back()
            # if result:
            #     self.press_pass()
            # else:
            #     self.press_pass(tof=False)
            #
            # self.raw_cmd('shell','svc','wifi','enable')
            # self.clicktext(text="WiFi configuration lockdown")
            # time.sleep(2)
            # self.d.press.back()
            # time.sleep(2)
            self.raw_cmd('shell', 'input', 'text', 'PENGUIN')
            time.sleep(3)
            self.d.press.back()
            self.clicktext(text="WPA")
            self.clicktext(text="CREATE WIFI CONFIGURATION")
            time.sleep(2)
            self.clicktext(text="Unlocked config is modifiable in Settings")
            self.clicktext(text="WIFI CONFIG LOCKDOWN OFF")
            self.clicktext(text="GO TO WIFI SETTINGS")
            time.sleep(5)
            self.d(text="PENGUIN").long_click()
            result = self.d(textStartsWith="Modify").exists
            result = result & (self.d(textStartsWith="Connect to network").exists)
            self.d.press.back()
            self.d.press.back()
            if result:
                self.press_pass()
            else:
                self.press_pass(tof=False)

            self.d(text="Locked config is not modifiable in Settings").click()
            self.d(text="WIFI CONFIG LOCKDOWN ON").click()
            self.d(text="GO TO WIFI SETTINGS").click()
            time.sleep(5)
            self.d(text="PENGUIN").long_click()
            time.sleep(1)
            result = not self.d(textStartsWith="Modify").exists
            result = result  & (not self.d(textStartsWith="Forget").exists)
            self.d.press.back()
            self.d.press.back()
            if result:
                self.press_pass()
            else:
                self.press_pass(tof=False)

            self.findtext("Locked config can be connected to")
            self.d(text="WIFI CONFIG LOCKDOWN ON").click()
            self.d(text="GO TO WIFI SETTINGS").click()
            time.sleep(5)
            self.d(text="PENGUIN").long_click()
            result = self.d(textStartsWith="Connect to network").exists
            print "result:",result
            self.d.press.back()
            self.d.press.back()
            if result:
                self.press_pass()
            else:
                self.press_pass(tof=False)

            self.findtext("Unlocked config can be forgotten")
            self.d(text="WIFI CONFIG LOCKDOWN OFF").click()
            self.d(text="GO TO WIFI SETTINGS").click()
            time.sleep(5)
            self.d(text="PENGUIN").long_click()
            result = self.d(textStartsWith="Forget network").exists
            self.d.press.back()
            self.d.press.back()
            if result:
                self.press_pass()
            else:
                self.press_pass(tof=False)
            self.press_pass()

            self.findtext("Disallow configuring WiFi")
            self.d(text="SET RESTRICTION").click()
            self.d(text="GO").click()
            result = (not self.d(textStartsWith="PENGUIN").exists) and (self.d(textStartsWith="More details").exists)
            self.d.press.back()
            if result:
                self.press_pass()
            else:
                self.press_pass(tof=False)
            self.findtext("Disallow configuring VPN")
            self.d(text="SET VPN RESTRICTION").click()
            self.d(text="GO").click()
            result = self.d(textStartsWith="More details").exists
            self.d.press.back()
            self.d(text="CHECK VPN").click()
            result = result & ("Cannot" in self.d(textStartsWith="Cannot establish").text)
            self.d.press.back()
            if result:
                self.press_pass()
            else:
                self.press_pass(tof=False)

            self.findtext("Disallow data roaming")
            self.d(text="SET RESTRICTION").click()
            self.d(text="GO").click()
            if self.d(text="Mobile network").exists:
                self.d(text="Mobile network").click()
            if self.d(text="ALWAYS").exists:
                self.d(text="ALWAYS").click()
            result  = not self.d(textStartsWith="Roaming").enabled
            result = result & self.d(textStartsWith="Roaming").click()
            result = result & (self.d(textStartsWith="More details").exists)
            self.d.press.back()
            self.d.press.back()
            if result:
                self.press_pass()
            else:
                self.press_pass(tof=False)

            self.findtext("Disallow factory reset")
            self.d(text="SET RESTRICTION").click()
            self.startapp("com.android.settings", "com.android.settings.Settings")
            time.sleep(1)
            self.findtext("System")
            self.findtext("Reset")
            self.d(textStartsWith="Erase all data").click()
            result =(self.find_template("Actionnotallowed.720x1440.png") != None)

            self.d.press.back()
            self.d.press.back()
            self.d.press.back()
            self.back2Verify()
            if result:
                self.press_pass()
            else:
                self.press_pass(tof=False)

            self.findtext("Disallow configuring Bluetooth")
            self.d(text="SET RESTRICTION").click()
            self.d(text="GO").click()
            self.d(resourceId="com.android.settings:id/switch_bar").click()
            result = (self.find_template("Actionnotallowed.720x1440.png") != None)

            self.d.press.back()
            self.d.press.back()
            if result:
                self.press_pass()
            else:
                self.press_pass(tof=False)

            self.findtext("Disallow USB file transfer")
            self.d(text="SET RESTRICTION").click()
            self.d.open.notification()
            time.sleep(1)
            self.d(textStartsWith="USB charging this device").click()
            if self.d(textStartsWith="Tap for").exists:
                self.d(textStartsWith="Tap for").click()
            self.d(text="Transfer files").click()
            result = (self.find_template("Actionnotallowed.720x1440.png") != None)
            self.d(textStartsWith="Transfer photos").click()
            result = result & self.d(textStartsWith="Action not allowed").exists
            result = result & (self.d(textStartsWith="More details").exists)
            self.d.press.back()
            self.d.press.back()
            if result:
                self.press_pass()
            else:
                self.press_pass(tof=False)

            self.findtext("Disable status bar")
            self.d(text="DISABLE STATUS BAR").click()
            time.sleep(2)
            self.d.open.notification()
            time.sleep(1)
            result = not self.d(textStartsWith="Android System").exists
            self.d(text="REENABLE STATUS BAR").click()
            time.sleep(1)
            self.d.open.notification()
            time.sleep(1)
            result = result & self.d(textStartsWith="Android System").exists
            self.d.press.back()
            if result:
                self.press_pass()
            else:
                self.press_pass(tof=False)

            self.findtext("Disable keyguard")
            self.d(text="DISABLE KEYGUARD").click()
            self.d.sleep()
            time.sleep(2)
            self.d.wakeup()
            time.sleep(2)
            result = self.d(textStartsWith="DISABLE KEYGUARD").exists
            self.d(text="REENABLE KEYGUARD").click()
            self.d.sleep()
            time.sleep(2)
            cmds = ['adb'] + ['-s'] + [self.serial] + ['shell', 'dumpsys', 'window', 'policy', '|grep',
                                                       'isStatusBarKeyguard']
            islock = subprocess.Popen(cmds, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()[0]
            result =  "=true" in islock
            self.d.wakeup()
            self.d.swipe(500, 700, 500, 100, steps=10)
            time.sleep(2)
            result = result & self.d(textStartsWith="REENABLE KEYGUARD").exists
            if result:
                self.press_pass()
            else:
                self.press_pass(tof=False)

            self.findtext("Setting the user icon")
            self.clicktext(text="SET USER ICON")
            time.sleep(2)
            self.clicktext(text="GO")
            self.findtext("Users")
            self.clicktext(text="Signed in as Owner")
            time.sleep(3)
            fi = self.find_template("verify_icon.720x1440.png")
            self.d.press.back()
            self.d.press.back()
            self.d.press.back()
            if fi != None:
                self.press_pass()
            else:
                self.press_pass(tof=False)

            os.system(
                'adb -s ' + self.serial + ' install -r ' + os.getcwd() + '/android-cts-verifier_8.1/CtsPermissionApp.apk')
            self.findtext("Permissions lockdown")
            if self.d(text="Grant").exists:
                self.d(text="Grant",className="android.widget.RadioButton").click()
                self.clicktext(text="OPEN APPLICATION SETTINGS")
                time.sleep(2)
                self.clicktext(text="Permissions")
                time.sleep(2)
                result1 = not self.d(text="Contacts").enabled
                time.sleep(1)
                self.d(text="Contacts").click()
                time.sleep(1)
                result1 = result1 & ("Action not allowed" in self.d.dump())
                if result1:
                    time.sleep(1)
                    result1 = result1 & ("More details" in self.d.dump())
                    self.d.press.back()
                    self.d.press.back()
                    self.d.press.back()
                print result1,"result"
                self.d(text="Let user decide", className="android.widget.RadioButton").click()
                self.clicktext(text="OPEN APPLICATION SETTINGS")
                time.sleep(2)
                self.clicktext(text="Permissions")
                time.sleep(1)
                result2 = self.d(text="Contacts").enabled
                time.sleep(1)
                result2 = result2 & self.d(resourceId="android:id/switch_widget").enabled
                self.d.press.back()
                self.d.press.back()
                print result2, "result2"
                self.d(text="Deny", className="android.widget.RadioButton").click()
                self.d(text="OPEN APPLICATION SETTINGS").click()
                time.sleep(2)
                self.d(text="Permissions").click()
                time.sleep(1)
                result3 = not self.d(text="Contacts").enabled
                time.sleep(1)
                self.d(text="Contacts").click()
                time.sleep(1)
                result3 = result3 & ("Action not allowed" in self.d.dump())
                print result3, "result3"
                if result3:
                    time.sleep(1)
                    result3 = result3 & ("More details" in self.d.dump())
                    self.d.press.back()
                    self.d.press.back()
                    self.d.press.back()
                    print result3, "result31"
                if result1 & result2 & result3:
                    self.press_pass()
                    time.sleep(1)
                else:
                    self.press_pass(tof=False)
                    time.sleep(1)
            self.findtext("Policy transparency test")
            self.findtext(text="Disallow add user")
            if self.d(resourceId= "com.android.cts.verifier:id/switch_widget").text=="OFF":
                self.d(resourceId= "com.android.cts.verifier:id/switch_widget").click()
            time.sleep(1)
            self.clicktext(text="OPEN SETTINGS")
            self.findtext("Users & accounts")
            result1 = not self.d(text="Add users from lock screen").enabled
            self.clicktext(text="Add users from lock screen")
            result1 = result1 & ("Action not allowed" in self.d.dump())
            result1 = result1 & ("More details" in self.d.dump())
            self.d.press.back()
            self.d.press.back()
            self.d.press.back()
            if result1 != None:
                self.press_pass()
            else:
                self.press_pass(tof=False)


            self.findtext(text="Disallow adjust volume")
            if self.d(resourceId="com.android.cts.verifier:id/switch_widget").text == "OFF":
                self.d(resourceId="com.android.cts.verifier:id/switch_widget").click()
            time.sleep(1)
            self.clicktext(text="OPEN SETTINGS")
            result1 = not (self.d(text="Media volume").enabled)
            result1 =  result1 & (not self.d(text="Alarm volume").enabled)
            result1 =  result1 & (not self.d(text="Ring volume").enabled)
            self.clicktext(text="Media volume")
            result1 = result1 & ("Action not allowed" in self.d.dump())
            result1 = result1 & ("More details" in self.d.dump())
            self.d.press.back()
            self.d.press.back()
            if result1 != None:
                self.press_pass()
            else:
                self.press_pass(tof=False)
            self.findtext(text="Disallow controlling apps")
            if self.d(resourceId="com.android.cts.verifier:id/switch_widget").text == "OFF":
                self.d(resourceId="com.android.cts.verifier:id/switch_widget").click()
            time.sleep(1)
            self.clicktext(text="OPEN SETTINGS")
            time.sleep(2)
            self.d(resourceId= "android:id/title").click()
            time.sleep(2)
            if self.d(text="DISABLE").enabled:
                self.clicktext(text="DISABLE")
                time.sleep(1)
                result1 = "Action not allowed" in self.d.dump()
                self.d.press.back()
            time.sleep(1)
            if self.d(text="FORCE STOP").enabled:
                time.sleep(1)
                self.clicktext(text="FORCE STOP")
                result1 = "Action not allowed" in self.d.dump()
                self.d.press.back()
                self.d.press.back()
            self.findtext("uiautomator")
            self.clicktext(text="UNINSTALL")
            time.sleep(1)
            result1 = result1 & ("Action not allowed" in self.d.dump())
            self.d.press.back()
            self.d.press.back()
            self.d.press.back()
            if result1 != None:
                self.press_pass()
            else:
                self.press_pass(tof=False)

            self.findtext(text="Disallow data roaming")
            result1 = False
            self.d(text="SET RESTRICTION").click()
            self.d(text="GO").click()
            time.sleep(1)
            if not self.d(text="Roaming").enabled:
                self.clicktext(text="Roaming")
                time.sleep(1)
                result1 = "Action not allowed" in self.d.dump()
                self.d.press.back()
            self.d.press.back()
            if result1 != None:
                self.press_pass()
            else:
                self.press_pass(tof=False)

            self.findtext(text="Disallow factory reset")
            result1 = False
            self.d(text="SET RESTRICTION").click()
            self.startapp("com.android.settings", "com.android.settings.Settings")
            time.sleep(1)
            self.findtext(text="System")
            self.findtext(text="Reset")
            if not self.d(text="Erase all data (factory reset)").enabled:
                self.clicktext(method="textStartsWith",text="Erase")
                time.sleep(1)
                result1 = "Action not allowed" in self.d.dump()
                self.d.press.back()
                self.d.press.back()
            self.d.press.back()
            if result1 != None:
                self.press_pass()
            else:
                self.press_pass(tof=False)

        finally:
            pass
            # self.press_pass()

    def test_DeviceOwneNTTest(self):
        print "No Device Owner Tests"
        if not (self.findtext("No Device Owner Tests")):
            print "No Device Owner Tests not found!"
            return 0
        self.clicktext(text="Device owner provisioning")
        time.sleep(1)
        self.clicktext(text="START PROVISIONING")
        if ("Contact your admin for help") in self.d.dump():
            self.d.press.back()
            self.press_pass()
        else:
            self.press_pass(tof=False)

        self.clear_notification()
        self.clicktext(text="Quick settings disclosure")
        time.sleep(1)
        self.d.open.quick_settings()
        result = self.d(text="managed").exists
        self.d.press.back()
        self.d.press.back()
        if result:
            self.press_pass()
        else:
            self.press_pass(tof=False)

        self.clicktext(text="Keyguard disclosure")
        self.clicktext(text="GO")
        result = self.d(text="managed").exists
        self.d.press.back()
        self.d.press.back()
        if result:
            self.press_pass()
        else:
            self.press_pass(tof=False)

    def someback(self):
        for i in xrange(0,3):
            self.d.press.back()
if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    testsuit = unittest.TestSuite()
    testsuit.addTest(CTSTest('test_BatterySaving'))
    testsuit.addTest(CTSTest('test_CameraFormatTest'))
    testsuit.addTest(CTSTest('test_CameraIntentTest'))
    testsuit.addTest(CTSTest('test_CameraOrientation'))
    testsuit.addTest(CTSTest('test_CameraVideo'))
    testsuit.addTest(CTSTest('test_CameraITSTest'))
    #testsuit.addTest(CTSTest('test_AdminInsatll'))
    testsuit.addTest(CTSTest('test_CarDock'))
    testsuit.addTest(CTSTest('test_Alarms'))
    testsuit.addTest(CTSTest('test_DeviceAdmin'))
    testsuit.addTest(CTSTest('test_Keyguard'))
    testsuit.addTest(CTSTest('test_Policy'))
    #testsuit.addTest(CTSTest('test_DeviceOwner'))
    #testsuit.addTest(CTSTest('test_DeviceOwneTest'))
    testsuit.addTest(CTSTest('test_DeviceOwneNTTest'))
    testsuit.addTest(CTSTest('test_Redacted'))
    testsuit.addTest(CTSTest('test_ScreenLock'))
    testsuit.addTest(CTSTest('test_Hardware'))
    testsuit.addTest(CTSTest('test_Companion'))
    testsuit.addTest(CTSTest('test_GNSS'))
    testsuit.addTest(CTSTest('test_ConnectivityConstraints'))

    testsuit.addTest(CTSTest('test_LocationOff'))
    #testsuit.addTest(CTSTest('test_BYODManaged'))
    #testsuit.addTest(CTSTest('test_BYOD_Provisioning'))
    runner.run(testsuit)

   # runner.find_template("verify_icon.720x1440.png")


