import atx
import subprocess
import sys,time
import unittest


class GFXTest(unittest.TestCase):

    def setUp(self):
        self.serial = "SS65IZJF8PDQEQYD"
        self.d = atx.connect(self.serial)
        self.d.press.back()

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

    def getLog(self):
        try:
            # out = self.raw_cmd('wait-for-device', 'shell', 'logcat', '-c',stdout=subprocess.PIPE)
            out = self.raw_cmd('wait-for-device', 'shell',
                               'logcat -d |grep -1 20 -E \"FATAL EXCEPTION|ANR in|CRASH:|NOT RESPONDING\"')
            outline = out.split("\r\n")
            find_crash = False
            for i in outline:
                if ("UiAutomation" in i) or ("ADB_SERVICES" in i):
                    continue
                if ("FATAL EXCEPTION" in i) or ("CRASH:" in i):
                    find_crash = True
                if find_crash:
                    find_crash = False
                    start = i.find("com")
                    end = i.find(',')
                    package = i[start:end].strip()
                    if " " in package:
                        package = package.split()[0]
                    pid = i[i.find("PID:"):].strip()
                    print "<" + str(self.serial) + "> " + package + "-> [CRASH]: " + i

                if ("ANR in" in i) or ("NOT RESPONDING:" in i):
                    start = i.find("com")
                    package = i[start:].strip()
                    # readini = self.readinit(os.getcwd() + '/' + str(s) + '.ini', "ANR", package)
                    print "<" + str(self.serial) + "> " + package + "-> [ANR]: " + i

        except Exception, e:
            pass

    def t1(self):
        self.d(scrollable=True).scroll.horiz.forward(steps=30)
        self.d(text="Add App").click()
        app =""
        if self.d(resourceId = "com.ape.easymode:id/check_box")[0].info.get("checked"):
            app = self.d(resourceId = "com.ape.easymode:id/app_name")[0].info.get("text")
            self.d.press.back()
        else:
            app = self.d(resourceId="com.ape.easymode:id/app_name")[0].info.get("text")
            self.d(resourceId="com.ape.easymode:id/check_box")[0].click()
            self.d(resourceId= "com.ape.easymode:id/ok_btn").click()
        time.sleep(0.5)
        if not self.d(text=app).exists:
            print "1 ko"
            raise AssertionError()

        self.d(text="Add App").click()
        if self.d(resourceId = "com.ape.easymode:id/check_box")[0].info.get("checked"):
            self.d(resourceId="com.ape.easymode:id/check_box")[0].click()
            self.d(resourceId="com.ape.easymode:id/ok_btn").click()
            self.d.press.back()
        else:
            self.d.press.back()
        time.sleep(0.5)
        if self.d(text='Chrome').exists:
            print "1 ko"
            raise AssertionError()

        print "1 ok"

    def t2(self):

        outinstall = self.raw_cmd('wait-for-device', 'shell', 'pm', 'list', 'package', 'com.xy.mobile.shaketoflashlight')
        if "com.xy.mobile.shaketoflashlight" not in outinstall:
            self.raw_cmd('wait-for-device', 'install', '-r', 'E:/s/base/apk/1.apk')
        time.sleep(1)
        self.d(scrollable=True).scroll.horiz.forward(steps=30)

        self.d(text="Add App").click()
        self.d(scrollable=True).scroll.to(text="Shake Flashlight")

        if self.d(text="Shake Flashlight").left(resourceId = "com.ape.easymode:id/check_box").info.get("checked"):
            self.d.press.back()
        else:
            self.d(text="Shake Flashlight").click()
            self.d(resourceId="com.ape.easymode:id/ok_btn").click()
        time.sleep(0.5)
        if not self.d(text="Shake Flashlight").exists:
            print "2 ko"
            raise AssertionError()

        self.d(text="Add App").click()
        self.d(scrollable=True).scroll.to(text="Shake Flashlight")

        if self.d(text="Shake Flashlight").left(resourceId = "com.ape.easymode:id/check_box").info.get("checked"):
            self.d(text="Shake Flashlight").click()
            self.d(resourceId="com.ape.easymode:id/ok_btn").click()
            self.d.press.back()
        else:
            self.d.press.back()
        time.sleep(0.5)
        if self.d(text="Shake Flashlight").exists:
            print "2 ko"
            raise AssertionError()
        print "2 ok"


    def t3(self):

        outinstall = self.raw_cmd('wait-for-device', 'shell', 'pm', 'list', 'package', 'com.xy.mobile.shaketoflashlight')
        if "com.xy.mobile.shaketoflashlight" not in outinstall:
            self.raw_cmd('wait-for-device', 'install', '-r', 'E:/s/base/apk/1.apk')
        self.d(scrollable=True).scroll.horiz.forward(steps=30)

        self.d(text="Add App").click()
        self.d(scrollable=True).scroll.to(text="Shake Flashlight")

        if self.d(text="Shake Flashlight").left(resourceId = "com.ape.easymode:id/check_box").info.get("checked"):
            self.d.press.back()
        else:
            self.d(text="Shake Flashlight").click()
            self.d(resourceId="com.ape.easymode:id/ok_btn").click()
        time.sleep(0.5)
        if not self.d(text="Shake Flashlight").exists:
            print "3 ko"
            raise AssertionError()


        #uninstall
        outinstall = self.raw_cmd('wait-for-device', 'shell', 'pm', 'list', 'package',
                                  'com.xy.mobile.shaketoflashlight')
        if "com.xy.mobile.shaketoflashlight" in outinstall:
            self.raw_cmd('wait-for-device', 'shell', 'pm', 'uninstall','com.xy.mobile.shaketoflashlight')
        time.sleep(1)
        self.d(scrollable=True).scroll.horiz.forward(steps=30)

        if self.d(text="Shake Flashlight").exists:
            print "3 ko"
            raise AssertionError()
        print "3 ok"

    def testback(self):
        self.d.press.home()
        time.sleep(1)
        if self.d(textContains="Use EasyMode").exists:
            self.d(text="Launcher3").click()
            time.sleep(1)

            if not self.d(text="Play Store").exists:
                print "back Launcher3 ko"
                raise AssertionError()
        self.d.press.home()
        time.sleep(1)
        if self.d(textContains="Use Launcher3").exists:
            self.d(text="EasyMode").click()
            time.sleep(1)

            if not self.d(text="Add App").exists:
                print "back EasyMode ko"
                raise AssertionError()

        self.d.press.home()
        if self.d(textContains="Use Launcher3").exists:
            self.d(text="EasyMode").click()
            time.sleep(1)


    def testloop(self):
        for i in xrange(0, 100):
            self.t1()
            self.t2()
            self.t3()
            self.testback()
            print i
            self.getLog()


if __name__=="__main__":
        unittest.main()

