#!/usr/bin/env python
# -*- coding: utf-8 -*-

import ConfigParser
import os
import subprocess
import sys
import re,time
from subprocess import Popen, PIPE

import schedule


class Config:
    def __init__(self, path):
        self.path = path
        self.cf = ConfigParser.ConfigParser()
        self.cf.read(self.path)

    def get(self, field, key):
        result = ""
        try:
            result = self.cf.get(field, key)
        except:
            result = ""
        return result

    def set(self, field, key, value):
        try:
            self.cf.set(field, key, value)
            self.cf.write(open(self.path, 'w'))
        except:
            return False
        return True

    def read_config(self, field, key):
        cf = ConfigParser.ConfigParser()
        try:
            cf.read(self.path)
            result = cf.get(field, key)
        except Exception, e:
            return "NONE"
        return result

    def write_config(self, field, key, value):
        cf = ConfigParser.ConfigParser()
        try:
            cf.read(self.path)
            cf.set(field, key, value)
            cf.write(open(self.path, 'w'))
        except:
            sys.exit(1)
        return True


class LogTest():
    def __init__(self):
        self.serials = self.getAdb()
        if (len(self.serials)) == 1:
            self.serial = self.serials[0]
        for i in self.serials:
            self.createIniFile(i)
            self.deleFile(i)

    def deleFile(self,se):
        self.raw_cmd('adb', '-s', str(se), 'wait-for-device', 'shell',
                     'rm -rf /data/tombstones/tombs* >/dev/null',
                     stdout=subprocess.PIPE).communicate()[0]

    def createIniFile(self,serial):
        file_object = open(os.getcwd() + '/' + str(serial) + '.ini', 'w')
        try:
            file_object.write('[ANR]\n')
            file_object.write('[CRASH]\n')
            file_object.write('[NE]\n')
        finally:
            file_object.close()

    def writeinit(self, filname, field, key, value):
        # print self.config.read_config(field, key)
        config = Config(filname)
        config.write_config(field, key, value)

    def readinit(self,filname, field, key):
        try:
            config = Config(filname)
            get = config.read_config(field, key)
            return get
        except Exception, e:
            return "NONE"

    def raw_cmd(self, *args, **kwargs):
        cmds = list(args)
        return subprocess.Popen(cmds, **kwargs)

    def getAdb(self):
        try:
            serial = []
            p = Popen("adb devices", shell=True, stdout=PIPE, stderr=PIPE)
            serial = p.stdout.readlines()
            if len(serial) == 3:
                serial = serial[1:-1]
                for i in range(len(serial)):
                    serial[i] = serial[i].replace("\t", "")
                    serial[i] = serial[i].replace("\n", "")
                    serial[i] = serial[i].replace("\r", "")
                    serial[i] = serial[i].replace("\r", "")
                    serial[i] = serial[i].replace("device", "")
                return serial
            elif len(serial) == 2:
                print "Device not found!"
                sys.exit(1)
            elif len(serial) >= 4:
                serials=[]
                for i in xrange(1,len(serial)-1):
                    serials.append(serial[i].split()[0])
                return serials
        except Exception, e:
            print "Device not found!"
            sys.exit(1)

    def getLog(self):
        try:
            for s in self.serials:
                # out = self.raw_cmd('wait-for-device', 'shell', 'logcat', '-c',stdout=subprocess.PIPE).communicate()[0]
                out = self.raw_cmd('adb','-s',str(s),'wait-for-device', 'shell', 'logcat -d |grep -A 1 -E \"FATAL EXCEPTION|ANR in|CRASH:|NOT RESPONDING\"',
                                   stdout=subprocess.PIPE).communicate()[0]
                outline = out.split("\r\n")
                find_crash = False
                tomstones = self.raw_cmd('adb', '-s', str(s), 'wait-for-device', 'shell',
                             'ls -r /data/tombstones/tombstone_*|head -n 1',
                             stdout=subprocess.PIPE).communicate()[0]

                if len(tomstones)>0:
                    tomstone = re.sub("\D", "", tomstones).replace("0", "")
                    self.writeinit(os.getcwd() + '/' + str(s) + '.ini', "NE", "Tombstone", tomstone)
                for i in outline:
                    if ("FATAL EXCEPTION" in i) or ("CRASH:" in i):
                        find_crash = True
                        continue
                    if find_crash:
                        find_crash = False
                        start = i.find("com")
                        end = i.find(',')
                        package = i[start:end].strip()
                        if " " in package:
                            package = package.split()[0]
                        pid = i[i.find("PID:"):].strip()
                        print str(s) + "-> [CRASH]: " + i
                        readini = self.readinit(os.getcwd() + '/' + str(s) + '.ini', "CRASH", package)
                        if "NONE" == readini:
                            self.writeinit(os.getcwd() + '/' + str(s) + '.ini', "CRASH", package, 1)
                        elif readini.isdigit():
                            readini = int(readini) + 1
                            self.writeinit(os.getcwd() + '/' + str(s) + '.ini', "CRASH", package, readini)
                    if ("ANR in" in i) or ("NOT RESPONDING:" in i):
                        start = i.find("com")
                        package = i[start:].strip()
                        readini = self.readinit(os.getcwd() + '/' + str(s) + '.ini', "ANR", package)
                        print str(s) + "-> [ANR]: " + i
                        if " " in package:
                            package = package.split()[0]
                        if "NONE" == readini:
                            self.writeinit(os.getcwd() + '/' + str(s) + '.ini', "ANR", package, 1)
                        elif readini.isdigit():
                            readini = int(readini) + 1
                            self.writeinit(os.getcwd() + '/' + str(s) + '.ini', "ANR", package, readini)
                            # self.writeinit()
        except Exception, e:
            sys.exit(1)
        finally:
            for m in self.serials:
                out = self.raw_cmd('adb','-s',str(m),'wait-for-device', 'shell', 'logcat', '-c', stdout=subprocess.PIPE).communicate()[0]


if __name__ == "__main__":
    test = LogTest()
    #test.getLog()
    schedule.every(15).minutes.do(test.getLog)
    while True:
        schedule.run_pending()
        time.sleep(1)
