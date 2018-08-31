#!/usr/bin/env python
# -*- coding: utf-8 -*-
from Tkinter import *
from subprocess import Popen, PIPE
import subprocess,time
import threading
class InitDevice():


    def testtk(self):
        t = threading.Thread(target=self.tktest).start()
        #k = threading.Thread(target=self.tktest).start()


    def testtime(self):
        while True:
            time.sleep(1)
            print time.time()


    def tktest(self):
        self.gettk()

    def gettk(self):
        root = Tk()
        root.geometry('600x500')
        root.title("GFXTest")
        helloLabel = Label(root, text='Please open GFX render in setting')
        helloLabel.pack()
        startButton = Button(root, text='Start', bg="pink")
        startButton.place(x=20, y=90, width=120, height=30)
        for i in xrange(0,10):

            root.update()
            print "good"
            time.sleep(1)

    def t2est(self,t="good"):
        print "test"
        print t
    def ap(self):
        lp=False
        p=0
        a=[1,2,3,4,"loop",2,3,"end",11,22,33]
        for k, v in enumerate(a):
            print "all",k,v
            if "loop" == v :
                lp = True
                continue
            if lp and "end" != k:
                p=k
                print "loop",k,v
            elif lp and "end" == k:

                lp =False




if __name__ == "__main__":
    test = InitDevice()
    #test.startthread()
    #test.testtime()
    test.gettk()


    # 主消息循环: