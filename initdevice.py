#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import subprocess
import sys
import threading
import time
from subprocess import Popen, PIPE

from uiautomator import Device

"am start -a android.settings.LOCALE_SETTINGS"

from Tkinter import *
class InitDevice():
    def __init__(self):
        self.serial = "HYUKV4DIAYJZGMRC"

    def getAdb(self):
        try:
            serial = []
            p = Popen("adb devices", shell=True, stdout=PIPE, stderr=PIPE)
            out = p.stdout.readlines()
            for i in range(len(out)):
                if "List" in out[i]:
                    continue
                if len(out[i]) > 5:
                    serial.append(out[i].split()[0])
            return serial
        except Exception, e:
            print "Device not found!"
            sys.exit(1)

    def raw_cmd(self, *args):
        try:
            timeout = 15
            Returncode = "over"
            cmds = ['adb'] + ['-s'] + [self.serial] + list(args)
            p = subprocess.Popen(cmds, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            c = p.communicate()[0]
            return c
        except Exception, e:
            pass

    def startthread(self):
        threads = []
        for i in self.serial:
            t = threading.Thread(target=self.inittest, args=(i,))
            t.setDaemon(False)
            threads.append(t)
        for i in xrange(len(self.serial)):
            threads[i].start()

        # for i in self.serial:
        #    self.inittest(i)

    def inittest(self, device):
        if sys.argv[1] =="p":
            self.pushres(device)
        else:
            d = Device(device)
            pkg = "com.tinno.autotesttool"
            os.system("adb -s " + device + " wait-for-device install -r " + os.getcwd() + "/lib/bundle/AutoTestTool.apk")

            cmds = ['adb'] + ['-s'] + [device] + ['wait-for-device', 'shell', 'pm', 'grant', pkg,
                         'android.permission.ACCESS_COARSE_LOCATION']
            p = subprocess.Popen(cmds, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()[0]

            cmds = ['adb'] + ['-s'] + [device] + ['wait-for-device', 'shell', 'pm', 'grant', pkg,
                                                      'android.permission.READ_EXTERNAL_STORAGE']
            p = subprocess.Popen(cmds, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()[0]

            cmds = ['adb'] + ['-s'] + [device] + ['wait-for-device', 'shell', 'pm', 'grant', pkg,
                                                  'android.permission.WRITE_EXTERNAL_STORAGE']
            p = subprocess.Popen(cmds, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()[0]

            cmds = ['adb'] + ['-s'] + [device] + ['wait-for-device', 'shell', 'pm', 'grant', pkg,
                                                  'android.permission.READ_CONTACTS']
            p = subprocess.Popen(cmds, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()[0]

            cmds = ['adb'] + ['-s'] + [device] + ['wait-for-device', 'shell', 'pm', 'grant', pkg,
                                                  'android.permission.WRITE_CONTACTS']
            p = subprocess.Popen(cmds, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()[0]

            cmds = ['adb'] + ['-s'] + [device] + ['wait-for-device', 'shell', 'pm', 'grant', pkg,
                                                  'android.permission.CALL_PHONE']
            p = subprocess.Popen(cmds, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()[0]

            cmds = ['adb'] + ['-s'] + [device] + ['wait-for-device', 'shell', 'pm', 'grant', pkg,
                                                  'android.permission.RECORD_AUDIO']
            p = subprocess.Popen(cmds, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()[0]

            cmds = ['adb'] + ['-s'] + [device] + ['wait-for-device', 'shell', 'pm', 'grant', pkg,
                                                  'android.permission.READ_PHONE_STATE']
            p = subprocess.Popen(cmds, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()[0]

            cmds = ['adb'] + ['-s'] + [device] + ['wait-for-device', 'shell', 'pm', 'list', 'package',
                                                  'com.github.uiautomator']
            p = subprocess.Popen(cmds, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()[0]
            if "com.github.uiautomator" not in p:
                cmds = ['adb'] + ['-s'] + [device] + ['wait-for-device', 'install', '-r',  os.getcwd() + '/lib/bundle/app.apk']
                p = subprocess.Popen(cmds, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()[0]

            cmds = ['adb'] + ['-s'] + [device] + ['wait-for-device', 'shell', 'pm', 'list', 'package',
                                                  'com.github.uiautomator.test']
            p = subprocess.Popen(cmds, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()[0]
            if "com.github.uiautomator.test" not in p:
                cmds = ['adb'] + ['-s'] + [device] + ['wait-for-device', 'install', '-r',
                                                      os.getcwd() + '/lib/bundle/app-test.apk']
                p = subprocess.Popen(cmds, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()[0]


            cmds = ['adb'] + ['-s'] + [device] + ['wait-for-device', 'shell', 'am', 'start', '-S', '-W',
                         'com.tinno.autotesttool/com.tinno.autotesttool.AutoTestToolActivity']
            p = subprocess.Popen(cmds, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()[0]
            try:
                for j in xrange(0, 3):
                    d(resourceId="android:id/text1")[j].click()
                    time.sleep(1)
                    d(className="android.widget.EditText").set_text("100")  # set the text
                    time.sleep(1)
                    d(resourceId="android:id/button1").click()
                    time.sleep(20)
                    d.wait.idle()
                    d(resourceId="android:id/progress").wait.gone(timeout=60000)

                time.sleep(1)

                cmds = ['adb'] + ['-s'] + [device] + ['wait-for-device', 'shell', 'am', 'start', '-S', '-W',
                             'com.android.settings/com.android.settings.Settings']
                p = subprocess.Popen(cmds, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()[0]



                time.sleep(1)

                cmds = ['adb'] + ['-s'] + [device] + ['wait-for-device', 'shell', 'svc', 'wifi', 'enable']
                p = subprocess.Popen(cmds, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()[0]

                time.sleep(2)
                if (d(textContains="WLAN").exists):
                    d(textContains="WLAN").click()
                elif (d(textContains="Network").exists):
                    d(textContains="Network").click()
                    time.sleep(0.5)
                    if (d(textContains="Wi").exists):
                        d(textContains="Wi").click()
                time.sleep(1)
                for k in xrange(0, 3):
                    if not (d(text="PENGUIN").exists):
                        d(scrollable=True).scroll.vert.forward()
                    else:
                        break
                d(text="PENGUIN").click()
                time.sleep(1)
                if not (d(textContains="FORGET").exists):
                    d(className="android.widget.EditText").set_text("NA@789_wifi@27")
                    d(resourceId="android:id/button1").click()
                    time.sleep(1)
            except Exception, e:
                pass
            finally:
                d.press.back()
                d.press.home()
        print "push res file..."

    def pushres(self,serial):
        os.system(
            "adb -s " + serial + " wait-for-device push " + "\"D:\Travel\MTBFMYOS\data\localfile/apk\" /sdcard/")
        os.system(
            "adb -s " + serial + " wait-for-device push " + "\"D:\Travel\MTBFMYOS\data\localfile/Music\" /sdcard/")


if __name__ == "__main__":
    test = InitDevice()
    test.startthread()
