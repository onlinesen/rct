import logging
import time

import pytest
from uiautomator import Device
DUT=""
RESDUT=""
class TestDevice(object):

    @pytest.fixture
    def device(self):
        return Device(DUT),Device(RESDUT)

    def watch(self,device):
        device.watcher("AUTO_OK").when(resourceId="android:id/button1").when(text="OK") \
            .click(text="OK")
        device.watcher("permission").when(text="DENY").click(text="ALLOW")


    # @classmethod
    # def teardown_class(cls):
    #     td = TestDevice()
    #     d = td.device()
    #     td.startapp()
    #     time.sleep(5)
    #     d(resourceId="com.ape.weather3:id/btn_add").click()
    #     d(resourceId="com.ape.weather3:id/menu_edit").click()
    #     if d(text="Beijing").exists:
    #         d(text="Beijing").click()
    #         d(resourceId="com.ape.weather3:id/delete").click()
    #         d(text="OK").click()
    #     d.press.back()
    #     d.press.back()
    #     d.press.home()
    def press_pass(self, device,tof=True):
        try:
            time.sleep(2)
            if tof:
                if device(resourceId="com.android.cts.verifier:id/pass_button").enabled:
                    device(resourceId="com.android.cts.verifier:id/pass_button").click()
                else:
                    device(resourceId="com.android.cts.verifier:id/fail_button").click()
            else:
                device(resourceId="com.android.cts.verifier:id/fail_button").click()
        except Exception, e:
            return 0

    def findtext(self, device, text):
        try:
            if device(resourceId="android:id/list").exists:
                device(resourceId="android:id/list").scroll.to(textStartsWith=text)
            else:
                device(scrollable=True).scroll.to(textStartsWith=text)
            time.sleep(1)
            device(textStartsWith=text).click()
            return True
        except Exception, e:
            if "SCROLLABLE=true" in e.message:
                try:
                    device(textStartsWith=text).click()
                except Exception, e:
                    return False
                return True
            else:
                return False

    def startapp(self, device, appname):
        d=device
        d.press.home()
        d(text='Camera').click()
        d.press.back()
        d.press.back()
        d.press.back()
        d(text=appname).click()

    def test_CameraFormatTest(self, device):
        try:
            logging.info("test_CameraFormatTest")
            channel = ["NV21", "YV12"]
            camera = ["Camera 0", "Camera 1"]
            self.startapp(device,"CTS Verifer")
            time.sleep(2)
            res = []
            device(resourceId="com.android.cts.verifier:id/resolution_selection").click()
            time.sleep(2)
            for j in xrange(0, 5):
                tv = device(className="android.widget.TextView")
                for i in xrange(0, tv.count):
                    if str(tv[i].text) not in res:
                        res.append(str(tv[i].text))
                device(scrollable=True).scroll(steps=50)
                time.sleep(1)
            device.press.back()
            for j in camera:
                device(resourceId="com.android.cts.verifier:id/cameras_selection").click()
                if not (self.findtext(j)):
                    print "no", j, "found!"
                    device.press.back()
                    continue
                for k in channel:
                    device(resourceId="com.android.cts.verifier:id/format_selection").click()
                    if not (self.findtext(k)):
                        device.press.back()
                        continue
                    for i in res:
                        device(resourceId="com.android.cts.verifier:id/resolution_selection").click()
                        if not (self.findtext(i)):
                            device.press.back()
                            continue
        finally:
            self.press_pass()

    def add_city(self, device):
        self.startapp()
        time.sleep(3)
        device(resourceId="com.ape.weather3:id/btn_add").click()
        device(resourceId="com.ape.weather3:id/add_city").click()
        device(resourceId="com.ape.weather3:id/search").set_text("Beijing")
        assert device(resourceId="com.ape.weather3:id/city").wait.exists(timeout=15000)
        device(resourceId="com.ape.weather3:id/city").click()
        assert (device(text="Beijing")).wait.exists(timeout=15000)
        device(text="Beijing").click()
        device(resourceId="com.ape.weather3:id/tv_weather_temp").wait.exists(timeout=15000)
        tempt = device(resourceId="com.ape.weather3:id/tv_weather_temp").text
        assert int(tempt) > 20
        device.press.back()
        device.press.back()
