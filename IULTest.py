#!/usr/bin/env python
# -*- coding: utf-8 -*-
import datetime
import os
import subprocess
import sys
import time
import unittest

import HTMLTestRunner


class ParametrizedTestCase(unittest.TestCase):
    """ TestCase classes that want to be parametrized should
        inherit from this class.
    """

    def __init__(self, methodName='runTest', serial=None, filename=None):
        super(ParametrizedTestCase, self).__init__(methodName)
        self.serial = serial
        self.filename = filename

    @staticmethod
    def parametrize(testcase_klass, serial=None, filename=None):
        """ Create a suite containing all tests taken from the given
            subclass, passing them the parameter 'param'.
        """
        testloader = unittest.TestLoader()
        testnames = testloader.getTestCaseNames(testcase_klass)
        suite = unittest.TestSuite()
        for name in testnames:
            suite.addTest(testcase_klass(name, serial=serial, filename=filename))
        return suite


class testadd(unittest.TestCase):
    def __init__(self, methodName='runTest', serial=None, filename=None):
        super(testadd, self).__init__(methodName)
        self.serial = serial
        self.filename = filename
        self.fnl = ""
        self.lon = False

    def setUp(self):
        # self.serial = self.serial
        pass

    def test_app(self):
        self.raw_cmd('shell', 'logcat', '-c')
        out = self.raw_cmd('install', '-r', self.filename)
        time.sleep(1)
        install_result = out
        self.assertEqual(install_result, "Success")
        ddms = ""
        if install_result == "Success":
            launch_out = self.raw_cmd1('shell', 'logcat', '-d', '|grep', '-m', '1',
                                       'android.intent.action.PACKAGE_ADDED\ dat=package')
            for i in launch_out:
                if "package:" in i:
                    dms = i.split()
                    for k in dms:
                        if "package:" in k:
                            ddms = k
                            break
            if ":" in ddms:
                package = ddms.split(":")[1]
                out = self.raw_cmd('shell',
                                   'monkey', '-p', package, '-c', 'android.intent.category.LAUNCHER', '1')
                time.sleep(5)

                self.assertEqual(False, self.getLog())
                if self.lon == True:
                    out = self.raw_cmd('shell', 'pm', 'uninstall', package)
                print install_result, self.filename, out

    def tearDown(self):
        pass

    def getLog(self):
        try:
            out = self.raw_cmd('shell',
                               'logcat -d |grep -A 1 -E \"FATAL EXCEPTION|ANR in|CRASH:|NOT RESPONDING\"')
            outline = out.split("\r\n")
            find_crash = False
            exception = False
            for i in outline:
                if ("UiAutomation" in i) or ("ADB_SERVICES" in i):
                    continue
                if ("FATAL EXCEPTION" in i) or ("CRASH:" in i):
                    find_crash = True
                    exception = True
                    continue
                if find_crash:
                    out1 = self.raw_cmd('shell', 'logcat -d ')
                    ref = os.getcwd() + "/CRASH_" + str(
                        datetime.datetime.now().strftime("%m%d%H%M%S")) + ".txt"
                    with open(ref, 'w+') as file:
                        file.write(out1)
                    find_crash = False
                    start = i.find("com")
                    end = i.find(',')
                    package = i[start:end].strip()
                    if " " in package:
                        package = package.split()[0]
                    pid = i[i.find("PID:"):].strip()
                if ("ANR in" in i) or ("NOT RESPONDING:" in i):
                    out1 = self.raw_cmd('shell', 'logcat -d ')
                    ref = os.getcwd() + "/ANR_" + str(
                        datetime.datetime.now().strftime("%m%d%H%M%S")) + ".txt"
                    with open(ref, 'w+', encoding='utf8') as file:
                        file.write(out1)
                    start = i.find("com")
                    exception = True
                    package = i[start:].strip()
                    if " " in package:
                        package = package.split()[0]
        finally:
            return exception

    def raw_cmd(self, *args):
        try:
            cmds = ['adb'] + ['-s'] + [self.serial] + list(args)
            p = subprocess.Popen(cmds, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            c = p.communicate()[0].strip()
            return c
        except Exception, e:
            pass

    def raw_cmd1(self, *args):
        try:
            cmds = ['adb'] + ['-s'] + [self.serial] + list(args)
            p = subprocess.Popen(cmds, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            c = p.communicate()
            return c
        except Exception, e:
            pass

    def runTest(self):
        self.serial = self.serial

    def to_go(self, ln):
        try:
            self.lon = ln
            fp = file(os.path.split(os.path.realpath(sys.argv[0]))[0] + "\\launche.html", "wb")
            suite = unittest.TestSuite()
            runner = HTMLTestRunner.HTMLTestRunner(
                verbosity=0,
                stream=fp,
                title="AutoTraveler Report",
                description="OSTeam"
            )
            lst = os.listdir(self.filename)
            for i in lst:
                if i.endswith('.apk'):
                    suite.addTest(
                        ParametrizedTestCase.parametrize(testadd, serial=self.serial, filename=self.filename + "/" + i))
            runner.run(suite)
        except Exception, e:
            pass

            #
            # if __name__=="IULTest":
            #     filepath='E:\\work\GFXTest\\ab1.html'
            #     fp=file(filepath,'w+')
            #
            #     runner = HTMLTestRunner.HTMLTestRunner(stream=fp,title='sd',description='bb')
            #     runner.run(testadd("test_add1"))
            #     fp.close()
