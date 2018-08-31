import pytest
import os
import time
from uiautomator import Device
class TestDevice(object):

    @pytest.fixture
    def device(self):
        return Device()


    def startapp(self,d,app):
        d.press.back()
        d.click(text=app).click()

    def test_add_city(self,device):
        self.startapp(device,"CTS Verifier")
        time.sleep(2)
        print device(text="abc").exists








