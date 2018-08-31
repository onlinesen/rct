# /usr/bin/env python
# coding=utf8

import httplib
import md5
import urllib
import random
import urllib2
import json
import  re
import os

class MockFile():
    @staticmethod
    def rm(fn):
        if os.path.isfile(fn):
            os.remove(fn)
