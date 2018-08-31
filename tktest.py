#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import time
from Tkinter import *
import win32api
import win32event
import win32service
import win32serviceutil
import servicemanager
import os
from subprocess import Popen, PIPE
import subprocess,time
class MyService(win32serviceutil.ServiceFramework):

    _svc_name_ = "MyService"
    _svc_display_name_ = "My Service"
    _svc_description_ = "My Service"

    def __init__(self, args):
        self.log('init')
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self.root = Tk()
        self.root.geometry('600x500')
        self.root.title("GFXTest")
        self.log('init1')

    def SvcDoRun(self):
        self.ReportServiceStatus(win32service.SERVICE_START_PENDING)
        try:
            self.ReportServiceStatus(win32service.SERVICE_RUNNING)
            self.log('start')
            self.start()

            self.log('wait')
            win32event.WaitForSingleObject(self.stop_event, win32event.INFINITE)
            self.log('done')


        except BaseException as e:
            self.log('Exception : %s' % e)
            self.SvcStop()

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        self.log('stopping')
        self.stop()
        self.log('stopped')
        win32event.SetEvent(self.stop_event)
        self.ReportServiceStatus(win32service.SERVICE_STOPPED)

    def start(self):
        self.log('tk1')
        #os.system("python e:\\work\gfxtest\\tktest1.py")
        #cmds = ['python'] + ['-s'] + [self.serial] + list(args)
        p = subprocess.Popen(['E:\\work\\GFXTest\\dist\\tk.bat'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.log('st2')
        time.sleep(1)


    def stop(self):
        pass

    def log(self, msg):
        servicemanager.LogInfoMsg(str(msg))

    def sleep(self, minute):
        win32api.Sleep((minute*1000), True)

    def gettk(self):
        self.log('tk')
        helloLabel = Label(self.root, text='Please open GFX render in setting')
        helloLabel.pack()
        startButton = Button(self.root, text='Start', bg="pink")
        startButton.place(x=20, y=90, width=120, height=30)
        self.log('tk1')
        self.root.update()
        self.log('tk11')

if __name__ == "__main__":
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(MyService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(MyService)