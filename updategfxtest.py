#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import subprocess
import sys
import threading
import time
from subprocess import Popen, PIPE
import urllib

"am start -a android.settings.LOCALE_SETTINGS"


class UpdateGFXtest():
    def __init__(self):
        self.serial = self.getAdb()
    def Schedule(a, b, c):
        '''''
        a:已经下载的数据块
        b:数据块的大小
        c:远程文件的大小
       '''
        per = 100.0 * a * b / c
        if per > 100:
            per = 100
        print '%.2f%%' % per
    def update(self):
        url = 'http://www.python.org/ftp/python/2.7.5/Python-2.7.5.tar.bz2'
        # local = url.split('/')[-1]
        local = os.path.join('/data/software', 'Python-2.7.5.tar.bz2')
        urllib.urlretrieve(url, local, Schedule)

if __name__ == "__main__":
    test = InitDevice()
    test.startthread()
