#!/usr/bin/end python
# -*- coding: utf-8 -*-
from uiautomator import Device#导入uiautomator模块

class HelloWorld():#定义类

    def __init__(self):#构造函数，初始化类变量 d 赋予连接的设备
     self.d = Device("586558c7")

    def automationtest1_1(self):#函数1，打印字符
        print "Hello,world"

    def automationtest1_2(self):
        print self.d.info #打印设备状态
        self.d(text = "Settings").click()#点击文字
        self.d(text = "Connected devices").click()#点击资源Id
        print self.d(resourceId= "com.android.settings:id/switchWidget").checked #检查资源状态

if __name__=="__main__":
    hw = HelloWorld()#实例化对象hw，继承HelloWorld类
    hw.automationtest1_1()#使用类中的函数1
    hw.automationtest1_2()
