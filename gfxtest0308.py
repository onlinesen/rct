#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
  当渲染时间大于16.67，按照垂直同步机制，该帧就已经渲染超时
  那么，如果它正好是16.67的整数倍，比如66.68，则它花费了4个垂直同步脉冲，减去本身需要一个，则超时3个
  如果它不是16.67的整数倍，比如67，那么它花费的垂直同步脉冲应向上取整，即5个，减去本身需要一个，即超时4个，可直接算向下取整

  最后的计算方法思路：
  执行一次命令，总共收集到了m帧（理想情况下m=128），但是这m帧里面有些帧渲染超过了16.67毫秒，算一次jank，一旦jank，
  需要用掉额外的垂直同步脉冲。其他的就算没有超过16.67，也按一个脉冲时间来算（理想情况下，一个脉冲就可以渲染完一帧）

  所以FPS的算法可以变为：
  m / （m + 额外的垂直同步脉冲） * 60
  '''
import Queue
import collections
import datetime
import glob
import hashlib
import os
import random
import signal
import subprocess
import thread
import xml.dom.minidom
from Tkinter import *
from optparse import OptionParser, OptionGroup
from subprocess import Popen, PIPE
import tkFileDialog
import tkinter.filedialog
import tkinter.messagebox
from PIL import Image, ImageTk
from tkinter import ttk
from uiautomator import Device

import MinicapMin
from lib.imcp.mixin import DeviceMixin
from myocr import MYOCRTest

UINode = collections.namedtuple('UINode', [
    'xml',
    'bounds',
    'selected', 'checkable', 'clickable', 'scrollable', 'focusable', 'enabled', 'focused', 'long_clickable',
    'password',
    'class_name',
    'index', 'resource_id',
    'text', 'content_desc',
    'package'])
__boundstuple = collections.namedtuple('Bounds', ['left', 'top', 'right', 'bottom'])
FindPoint = collections.namedtuple('FindPoint', ['pos', 'confidence', 'method', 'matched'])

import threading
import time


class Bounds(__boundstuple):
    def __init__(self, *args, **kwargs):
        self._area = None

    def is_inside(self, x, y):
        v = self
        return x > v.left and x < v.right and y > v.top and y < v.bottom

    @property
    def area(self):
        if not self._area:
            v = self
            self._area = (v.right - v.left) * (v.bottom - v.top)
        return self._area

    @property
    def center(self):
        v = self
        return (v.left + v.right) / 2, (v.top + v.bottom) / 2

    def __mul__(self, mul):
        return Bounds(*(int(v * mul) for v in self))


class MyLogger(type(sys)):
    '''
    This class is used for printing colorful log
    '''
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50
    # NOTSET = 0
    WINDOWS_STD_OUT_HANDLE = -11
    GREEN_COLOR = 2
    RED_COLOR = 4
    YELLOW_COLOR = 6
    WHITE_COLOR = 7

    def __init__(self, *args, **kwargs):
        self.level = self.__class__.INFO
        self.output = "log_" + time.strftime("%m-%d-%H-%M",
                                             time.localtime()) + ".txt"

    # def __set_color(self, color):
    #     out_handler = ctypes.windll.kernel32.GetStdHandle(self.__class__.WINDOWS_STD_OUT_HANDLE)
    #     ctypes.windll.kernel32.SetConsoleTextAttribute(out_handler, color)

    def __log(self, level, fmt, *args, **kwargs):
        sys.stderr.write(
            '{0} {1} {2}\n'.format(level, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), fmt % args))
        if level >= self.level and self.output is not None:
            with open(self.output, 'a') as f:
                f.write('{0} {1} {2}\n'.format(level, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), fmt % args))

    def format(color, level):
        def wrapped(func):
            def log(self, fmt, *args, **kwargs):
                # self.__set_color(color)
                self.__log(level, fmt, *args, **kwargs)
                # self.__set_color(self.__class__.WHITE_COLOR)

            return log

        return wrapped

    def config(self, *args, **kwargs):
        if 'outfile' in kwargs:
            self.output = kwargs['outfile']

        if 'level' in kwargs:
            self.level = kwargs['level']
        else:
            self.level = int(kwargs.get('level', self.__class__.INFO))

    @format(GREEN_COLOR, 'DEBUG')
    def debug(self, fmt, *args, **kwargs):
        pass

    @format(WHITE_COLOR, 'INFO')
    def info(self, fmt, *args, **kwargs):
        pass

    @format(YELLOW_COLOR, 'WARNING')
    def warning(self, fmt, *args, **kwargs):
        pass

    @format(RED_COLOR, 'ERROR')
    def error(self, fmt, *args, **kwargs):
        pass

    @format(RED_COLOR, 'CRITICAL')
    def critical(self, fmt, *args, **kwargs):
        pass


class GFXTest():
    def __init__(self):
        # arg_parser = self.setup_arg_parser()
        # (self.options, self.args) = arg_parser.parse_args()
        # self.logger = MyLogger()
        # if self.options.campaign_name == "":
        #     self.options.campaign_name = "fps"
        # elif (self.options.campaign_name != "start") & (self.options.campaign_name != "fps"):
        #     self.options.campaign_name = "fps"
        # self.flag = True
        # self.campaign = self.options.campaign_name
        #
        # self.package = self.options.test_package
        # self.activity = self.options.pkg_activity
        self.screensave = 3
        self.numberChosen = None
        # self.gfxtest_gui = self.options.gfxtest_gui
        # self.xy = self.options.screen_xy
        self.scroll_xy = "v"
        self.scroll_direct = "v"
        self.platfrom_fps = "n"
        self.cpu_flag = True

        self.package = None
        self.apkversion = None
        self.buildversion = None
        self.fps_ave = 0
        self.WIDTH = None
        self.HEIGHT = None
        self.mem = ""
        self.cpu = ""
        self.cpu_max = []
        self.md5list = []
        self.cpu_flag = True
        self.q = Queue.Queue(0)
        self.enableFPS = "yes"
        self.d = None
        self.dm = None
        self.textout = None
        self.radionButton_value = None
        self.radionButton_rp_value = None
        self.typeRecord = None
        self.typeReplay = None
        self.typeManu = None
        self.typeSuper = None
        self.typeDirect = None
        self.packageEdit = ""
        # self.serial = self.options.serial_number
        self.fileEdit = "record.text"
        self.startX = 0
        self.startY = 0
        self.radiobutton = None
        self.imglabel = None
        self.radionButton_type_value = None
        self.root = None
        self.canvas = None
        self.canvas_performance = None
        self._mouse_motion = ""
        self._mouse_motion_crop = ""
        self._mouse_motion_xy = []
        self.cavas_x_y = {}
        self.crop_box = []

    def getAllPkg(self):
        try:
            allpkg = []
            out = self.raw_cmd('wait-for-device', 'shell', "pm list package |grep -E '(ape.)|(myos.)|(com.a)'")
            for k in (out.strip().split("\r")):
                pkg = k[k.find("package:") + 8:]
                allpkg.append(pkg)
            new_ls = sorted(allpkg, reverse=True)
            if len(new_ls) == 0:
                return [""]
            else:
                return new_ls
        except Exception, e:
            self.textout.insert(END, "出错了\n")
            self.textout.update()
            return [""]

    def getAllFile(self):
        allFile = []
        for filename in glob.glob(os.getcwd() + r'\*.txt'):
            allFile.append(filename)
        if len(allFile) == 0:
            return [""]
        else:
            return allFile

    def inidevice(self):
        if (self.package == None):
            self.package = self.getPackage()

        self.apkversion, self.buildversion = self.getAPKVersion()
        size = self.screenSize()
        self.WIDTH = int(size[0])
        self.HEIGHT = int(size[1])
        # self.killmonkey()
        self.d = Device(self.serial)
        self.dm = DeviceMixin(self.d)

    def gettk(self):
        self.root = Tk()
        self.root['bg'] = "White"
        self.root.geometry('1060x720+100+100')
        self.root.title("GFXTest 3.3.2")
        self.canvas = Canvas(self.root, bg="gray", bd=0, highlightthickness=0, relief='ridge')
        # self.canvas_performance = Canvas(self.root, bg="gray",  bd=0, highlightthickness=0, relief='ridge')
        # self.canvas_performance.place(x=0, y=450, width=220, height=320)

        self.canvas.bind("<Button-1>", self._mouse_click)
        self.canvas.bind("<B1-Motion>", self._stroke_move)
        self.canvas.bind("<B1-ButtonRelease>", self._stroke_done)
        # self.canvas.bind("<Motion>", self._mouse_move)
        self.canvas.place(x=700, y=0, width=360, height=720)

        totallable = Label(self.root, bg="MediumAquamarine", text='Tinno Performance Test Tool',
                           font=("Century", "16", "bold"))
        totallable.place(x=0, y=0, width=700, height=40)
        settingslable = Label(self.root, bg="MediumAquamarine", text='请手动打开设置中的GPU Rendering!', font=("Century"),
                              fg="Crimson")
        settingslable.place(x=0, y=695, width=700, height=25)

        serialRefresh = Label(self.root, bg="White", text='设备列表')
        serialRefresh.place(x=2, y=340, width=60, height=30)

        serial = self.getAdb2()
        self.radionButton_value = StringVar()
        for i in xrange(len(serial)):
            self.radionButton_value.set(serial[i])
            self.radiobutton = Radiobutton(self.root, bg="White", text=serial[i], variable=self.radionButton_value,
                                           value=serial[i],
                                           command=lambda: self.on_serial_select(self.root))
            # self.radiobutton.place(x=0, y=180 + 40 * i, width=200, height=30)
            self.radiobutton.place(x=0, y=380 + 30 * i)

        # startButton = Button(self.root, font=("Calibri", "10", "bold"), text='启动时间', bg="Orange", command=self.testLaunch)
        # startButton.place(x=51, y=55, width=105, height=35)

        clickxy = Label(self.root, bg="White", text='点击')
        clickxy.place(x=2, y=150, width=30, height=30)
        self.startX = Entry(self.root, bg="white")
        self.startX.place(x=35, y=150, width=50, height=30)
        x = Label(self.root, bg="White", text='x')
        x.place(x=92, y=150, width=10, height=30)
        self.startY = Entry(self.root, bg="white")
        self.startY.place(x=110, y=150, width=50, height=30)

        self.textout = Text(self.root, font=("Arial", "11"), bg="Black", fg="AntiqueWhite")
        self.textout.place(x=220, y=40, width=480, height=655)
        self.textout.insert("1.0", "输出信息窗口\n")

        if len(serial) == 1:
            self.serial = serial[0]
            size = self.screenSize()
            self.WIDTH = int(size[0])
            self.HEIGHT = int(size[1])
        elif len(serial) > 1:
            self.serial = self.radionButton_value.get()
            size = self.screenSize()
            self.WIDTH = int(size[0])
            self.HEIGHT = int(size[1])
        else:
            print "No any device!"
            self.textout.insert("1.0", "No any device found!\n")
            self.textout.update()

        self.typeRecord = IntVar()
        self.typeReplay = IntVar()
        self.typeManu = IntVar()
        self.typeSuper = IntVar()
        self.typeDirect = IntVar()
        manuButton = Checkbutton(self.root, bg="White", variable=self.typeDirect, text='水平', onvalue=1, offvalue=0)
        manuButton.place(x=2, y=190, width=50, height=30)

        self.radionButton_rp_value = StringVar()
        self.radionButton_rp_value.set("v")
        radiobuttonr = Radiobutton(self.root, bg="White", text="记录", variable=self.radionButton_rp_value,
                                   value="r",
                                   command=lambda: self.on_recordreplay_record(self.root))
        radiobuttonr.place(x=55, y=190, width=50, height=30)

        radiobuttonp = Radiobutton(self.root, bg="White", text="回放", variable=self.radionButton_rp_value,
                                   value="p",
                                   command=lambda: self.on_recordreplay_replay(self.root))
        radiobuttonp.place(x=110, y=190, width=50, height=30)

        radiobuttonm = Radiobutton(self.root, bg="White", text="手动", variable=self.radionButton_rp_value,
                                   value="m")
        radiobuttonm.place(x=165, y=190, width=50, height=30)

        radiobuttonm = Radiobutton(self.root, bg="White", text="控制", variable=self.radionButton_rp_value,
                                   value="s", command=lambda: self.on_super_replay(self.root))
        radiobuttonm.place(x=2, y=220, width=50, height=30)


        self.radionButton_type_value = StringVar()
        self.radionButton_type_value.set("fps")
        radiobuttone = Radiobutton(self.root, bg="White", text="流畅度FPS", variable=self.radionButton_type_value,
                                   value="fps",
                                   command=lambda: self.execute_select())
        radiobuttone.place(x=2, y=40, width=90, height=30)
        radiobuttone = Radiobutton(self.root, bg="White", text="启动时间", variable=self.radionButton_type_value,
                                   value="start",
                                   command=lambda: self.execute_select())
        radiobuttone.place(x=100, y=40, width=90, height=30)

        packageLabel = Label(self.root, bg="White", text='包名')
        packageLabel.place(x=2, y=70, width=30, height=30)
        number = StringVar()
        self.packageEdit = ttk.Combobox(self.root, width=40, textvariable=number)
        self.packageEdit['values'] = self.getAllPkg()  # 设置下拉列表的值
        self.packageEdit.place(x=35, y=70, width=178, height=30)  # 设置其在界面中出现的位置  column代表列   row 代表行
        self.packageEdit.current(0)

        fileLabel = Label(self.root, bg="White", text='文件')
        fileLabel.place(x=2, y=110, width=30, height=30)

        number = StringVar()
        self.fileEdit = ttk.Combobox(self.root, width=40, textvariable=number)
        self.fileEdit['values'] = self.getAllFile()  # 设置下拉列表的值
        self.fileEdit.place(x=35, y=110, width=178, height=30)  # 设置其在界面中出现的位置  column代表列   row 代表行
        self.fileEdit.current(0)

        number = StringVar()
        timeLabel = Label(self.root, bg="White", text='次数/时间')
        timeLabel.place(x=150, y=220, width=70, height=30)
        self.numberChosen = ttk.Combobox(self.root, width=12, textvariable=number)
        self.numberChosen['values'] = (1, 3, 5, 10, 20, 30, 100, 500, 1000)
        self.numberChosen.place(x=70, y=222, width=80, height=30)
        self.numberChosen.current(1)
        self.screensave = int(self.numberChosen.get())

        menubar = Menu(self.root)
        menubar.add_command(label='GO整机测试  |', command=self.platformRun2)
        menubar.add_command(label="刷新设备  |", command=lambda: self.on_serial_refresh(self.root))
        menubar.add_command(label="刷新界面  |", command=self.imagetk)
        menubar.add_command(label="帮助    |", command=self.help)
        menubar.add_command(label="BACK  |", command=self.press_back)
        menubar.add_command(label="HOME  |", command=self.press_home)
        menubar.add_command(label="POWER  |", command=self.press_power)
        menubar.add_command(label="截图  |", command=self.crop_image)
        execute_Button = Button(self.root, text='开始', bg="Orange", font=("黑体", "15"), command=self.execute_type)
        execute_Button.place(x=0, y=270, width=220, height=40)
        self.root['menu'] = menubar

        if self.installbundle():
            self.takeshot()
        if os.path.isfile(os.getcwd() + '/maintmp.png'):
            img = Image.open(os.getcwd() + '/maintmp.png')  # 打开图片
            w, h = img.size
            img = img.resize((360, 720), Image.ANTIALIAS)
            # image = img.copy()
            # image.thumbnail((324, 600), Image.ANTIALIAS)
            tkimage = ImageTk.PhotoImage(img)
            # self._tkimage = tkimage
            self.canvas.config(width=w, height=h)
            self.canvas.create_image(0, 0, anchor=tkinter.NW, image=tkimage)

        self.root.mainloop()

    def press_back(self):
        self.raw_cmd('wait-for-device', 'shell', 'input', 'keyevent 4')
        time.sleep(0.1)
        self.imagetk()

    def press_home(self):
        self.raw_cmd('wait-for-device', 'shell', 'input', 'keyevent 3')
        time.sleep(0.2)
        self.imagetk()

    def press_power(self):
        self.raw_cmd('wait-for-device', 'shell', 'input', 'keyevent 26')
        time.sleep(0.3)
        self.imagetk()

    def execute_type(self):
        zhixingfangshi = self.radionButton_type_value.get()

        if zhixingfangshi == "fps":
            self.gettest()
        else:
            self.testLaunch()

    def execute_select(self):
        zhixingfangshi = self.radionButton_type_value.get()
        if zhixingfangshi == "fps":
            self.textout.delete("1.0", END)
            self.textout.insert(END, "当前设备：" + self.serial + "\n")
            self.textout.insert(END, "选择了：流畅度【FPS测试】\n")
            self.textout.update()
        else:
            self.textout.delete("1.0", END)
            self.textout.insert(END, "当前设备：" + self.serial + "\n")
            self.textout.insert(END, "选择了：启动时间【截图】\n")
            self.textout.update()

    def help(self):
        self.textout.delete("1.0", END)
        self.textout.insert("1.0", "当前设备：" + self.serial + "\n")
        self.textout.insert("1.0", "Gfxtest 工具用于测试应用的GFXInfo信息和应用启动时间。\n")
        self.textout.update()

    def on_serial_select(self, tk):
        self.serial = self.radionButton_value.get()
        size = self.screenSize()
        self.WIDTH = int(size[0])
        self.HEIGHT = int(size[1])
        self.textout.delete("1.0", END)
        self.textout.insert("1.0", "当前设备：" + self.serial + "\n")
        self.textout.update()
        number = StringVar()
        self.packageEdit = ttk.Combobox(tk, width=40, textvariable=number)
        self.packageEdit['values'] = self.getAllPkg()  # 设置下拉列表的值
        self.packageEdit.place(x=35, y=70, width=178, height=30)  # 设置其在界面中出现的位置  column代表列   row 代表行
        self.packageEdit.current(0)
        self.startX.delete(0, END)
        self.startY.delete(0, END)
        self.installbundle()
        self.imagetk()

    def on_serial_refresh(self, tk):
        self.radionButton_rp_value.set("v")
        serial = self.getAdb2()
        self.startX.delete(0, END)
        self.startY.delete(0, END)
        if len(serial) == 1:
            self.serial = serial[0]
            size = self.screenSize()
            self.WIDTH = int(size[0])
            self.HEIGHT = int(size[1])
        elif len(serial) > 1:
            self.serial = self.radionButton_value.get()
            size = self.screenSize()
            self.WIDTH = int(size[0])
            self.HEIGHT = int(size[1])
        else:
            print "No any device!"
            self.textout.insert("1.0", "No any device found!\n")
            self.textout.update()

        self.radionButton_value = StringVar()
        for i in xrange(len(serial)):
            self.radionButton_value.set(serial[i])
            self.radiobutton = Radiobutton(tk, bg="White", text=serial[i], variable=self.radionButton_value,
                                           value=serial[i],
                                           command=lambda: self.on_serial_select(tk))
            self.radiobutton.place(x=0, y=380 + 30 * i)
        self.installbundle()
        self.imagetk()
        self.textout.delete(1.0, END)
        self.textout.insert(1.0, "当前设备：" + self.radionButton_value.get() + "\n")
        self.textout.update()

    def on_super_replay(self, tk):
        tkinter.messagebox.showinfo(title="提示框",
                                    message="输入测试脚本文件:\n" + "[功能列表：]\n"
                                            + "sleep\n"
                                            + "presshome\n"
                                            + "pressback\n"
                                            + "swipe:100,200,100,300\n"
                                            + "drag:100,200,100,300\n"
                                            + "checktext:text\n"
                                            + "checkimage:image.png\n"
                                            + "clickscreen:200x300\n"
                                            + "clicktext:text\n"
                                            + "clickimage:image.png\n"
                                            + "reboot\n"
                                            + "ocrface\n"
                                            + "ocrtext:text\n"
                                    )

    def on_recordreplay_record(self, tk):
        self.scroll_direct = "v"
        self.scroll_xy = "r"
        self.raw_cmd('wait-for-device', 'push', os.getcwd() + '/lib/bundle/eventrec', '/data/local/tmp/')
        time.sleep(0.1)
        self.raw_cmd('wait-for-device', 'shell', 'chmod', '777', '/data/local/tmp/eventrec')
        if self.fileEdit.get() == "":
            tkinter.messagebox.showinfo(title="提示框", message="录制回放可以输入文件，默认temp.txt \n 请点击[START]开始！")

    def on_recordreplay_replay(self, tk):
        self.scroll_direct = "v"
        self.scroll_xy = "p"
        self.raw_cmd('wait-for-device', 'push', os.getcwd() + '/lib/bundle/eventrec', '/data/local/tmp/')
        time.sleep(0.1)
        self.raw_cmd('wait-for-device', 'shell', 'chmod', '777', '/data/local/tmp/eventrec')
        if self.fileEdit.get() == "":
            tkinter.messagebox.showinfo(title="提示框", message="录制回放可以输入文件，默认temp.txt \n 请点击[START]开始！")


    def getLog(self, pkg):
        try:
            # out = self.raw_cmd('wait-for-device', 'shell', 'logcat', '-c',stdout=subprocess.PIPE)
            out = self.raw_cmd('wait-for-device', 'shell',
                               'logcat -d |grep -A 1 -E \"FATAL EXCEPTION|ANR in|CRASH:|NOT RESPONDING\"')
            outline = out.split("\r\n")
            find_crash = False
            # tomstones = self.raw_cmd('wait-for-device', 'shell',
            #                          'ls -r /data/tombstones/tombstone_*|head -n 1')

            # if len(tomstones) > 0:
            #     tomstone = re.sub("\D", "", tomstones).replace("0", "")
            #     # self.writeinit(os.getcwd() + '/' + str(s) + '.ini', "NE", "Tombstone", tomstone)
            #     self.logger.info("<" + pkg + ">" + " < Tombstone:" + str(tomstone) + " >")
            #     print str(self.serial) + "-> [TOMSTONES]: " + str(tomstone)
            for i in outline:
                if ("UiAutomation" in i) or ("ADB_SERVICES" in i):
                    continue
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
                    # print "<" + str(self.serial) + "> " + package + "-> [CRASH]: " + i
                    # readini = self.readinit(os.getcwd() + '/' + str(s) + '.ini', "CRASH", package)
                    # if "NONE" == readini:
                    #     self.writeinit(os.getcwd() + '/' + str(s) + '.ini', "CRASH", package, 1)
                    # elif readini.isdigit():
                    #     readini = int(readini) + 1
                    #     self.writeinit(os.getcwd() + '/' + str(s) + '.ini', "CRASH", package, readini)
                    self.logger.info("<" + pkg + ">" + " < CRASH:" + str(i) + " >")
                if ("ANR in" in i) or ("NOT RESPONDING:" in i):
                    start = i.find("com")
                    package = i[start:].strip()
                    # readini = self.readinit(os.getcwd() + '/' + str(s) + '.ini', "ANR", package)
                    print "<" + str(self.serial) + "> " + package + "-> [ANR]: " + i
                    if " " in package:
                        package = package.split()[0]
                        # if "NONE" == readini:
                        #     self.writeinit(os.getcwd() + '/' + str(s) + '.ini', "ANR", package, 1)
                        # elif readini.isdigit():
                        #     readini = int(readini) + 1
                        #     self.writeinit(os.getcwd() + '/' + str(s) + '.ini', "ANR", package, readini)
                        #     # self.writeinit()
                    self.logger.info("<" + pkg + ">" + " < ANR:" + str(i) + " >")
        except Exception, e:
            self.textout.insert(END, "出错了\n")
            self.textout.update()
        finally:
            out = self.raw_cmd('wait-for-device', 'shell', 'logcat', '-c')

    def installbundle(self):
        # self.killsh()
        # self.raw_cmd('wait-for-device', 'shell', 'dumpsys', 'SurfaceFlinger  --latency-clear')
        # out1 = self.raw_cmd('wait-for-device', 'shell','ls','/data/local/tmp/bundle.jar')
        try:
            out1 = subprocess.check_output(
                "adb -s " + self.serial + " wait-for-device shell ls /data/local/tmp/bundle.jar; exit 0",
                stderr=subprocess.STDOUT, shell=True)
            if "No such" in out1:
                self.raw_cmd('wait-for-device', 'push', os.getcwd() + '/lib/bundle/bundle.jar', '/data/local/tmp/')
                out = self.raw_cmd('wait-for-device', 'shell', 'ls /data/local/tmp/bundle.jar')
                time.sleep(1)
            out = subprocess.check_output(
                "adb -s " + self.serial + " wait-for-device shell ls /data/local/tmp/uiautomator-stub.jar; exit 0",
                stderr=subprocess.STDOUT, shell=True)
            if "No such" in out:
                self.raw_cmd('wait-for-device', 'push', os.getcwd() + '/lib/bundle/uiautomator-stub.jar',
                             '/data/local/tmp/')
                time.sleep(1)
            out = subprocess.check_output(
                "adb -s " + self.serial + " wait-for-device shell ls /data/local/tmp/busybox; exit 0",
                stderr=subprocess.STDOUT, shell=True)
            if "No such" in out:
                out = self.raw_cmd('wait-for-device', 'push', os.getcwd() + '/lib/bundle/busybox', '/data/local/tmp/')
                time.sleep(1)
            print "install test app,please wait..."

            outinstall = self.raw_cmd('wait-for-device', 'shell', 'pm', 'list', 'package', ' com.github.uiautomator')
            if "com.github.uiautomator" not in outinstall:
                self.raw_cmd('wait-for-device', 'install', '-r', os.getcwd() + '/lib/bundle/app.apk')

            outinstallest = self.raw_cmd('wait-for-device', 'shell', 'pm', 'list', 'package',
                                         'com.github.uiautomator.test')
            if "com.github.uiautomator.test" not in outinstallest:
                out = self.raw_cmd('wait-for-device', 'install', '-r', os.getcwd() + '/lib/bundle/app-test.apk')
                time.sleep(1)

                # out = self.raw_cmd('wait-for-device', 'push', os.getcwd() + '/lib/bundle/fps.sh', '/data/local/tmp/')
                # out = self.raw_cmd('wait-for-device', 'shell', 'chmod 777 /data/local/tmp/busybox')
                # out = self.raw_cmd('wait-for-device', 'shell', 'chmod 777 /data/local/tmp/fps.sh')
            cpu = self.raw_cmd('wait-for-device', 'shell', 'getprop', 'ro.product.cpu.abi')
            cpu = cpu.strip()
            sdk = self.raw_cmd('wait-for-device', 'shell', 'getprop', 'ro.build.version.sdk')
            sdk = sdk.strip()
            out = self.raw_cmd('wait-for-device', 'push', os.getcwd() + '/lib/' + sdk + '/' + cpu + '/minicap.so',
                               '/data/local/tmp/')
            out = self.raw_cmd('wait-for-device', 'push', os.getcwd() + '/lib/' + sdk + '/' + cpu + '/minicap',
                               '/data/local/tmp/')
            out = self.raw_cmd('wait-for-device', 'shell', 'chmod', '777', '/data/local/tmp/minicap')
            return True
        except Exception, e:
            return False

    def screenSize(self):
        out = self.raw_cmd('wait-for-device', 'shell', 'wm', 'size')
        out = out.split()[-1].split("x")
        return out

    def getPackage(self):
        out = self.shell_cmd('getprop ro.build.version.sdk')
        sdk = int(out.strip())
        if sdk < 26:
            getp = self.shell_cmd('dumpsys activity |grep mFocusedActivity')
        else:
            getp = self.shell_cmd('dumpsys activity |grep mResumedActivity')
        # out = self.raw_cmd('wait-for-device', 'shell', 'ps', '|grep', 'minicap')
        start = getp.find("com")
        end = getp.find('/')
        package = getp[start:end].strip()
        # apkversion = self.raw_cmd('wait-for-device', 'shell', 'dumpsys', "package", package, "|", "grep",'versionName', '|head -n 1')
        return package

    def getAPKVersion(self):
        buildversion = ""
        apkversion = ""
        buildversion = \
            self.raw_cmd('wait-for-device', 'shell', 'getprop', 'ro.custom.build.version').strip()
        apkversion = \
            self.raw_cmd('wait-for-device', 'shell', 'dumpsys', "package", self.package, "|", "grep", 'versionName')
        if "versionName=" in apkversion:
            apkversion = apkversion.replace("versionName=", "").strip().split()[0]
        if "_" in apkversion:
            apkversion = apkversion.split("_")[0]
        return apkversion, buildversion

    def getActivity(self):
        out = self.raw_cmd('wait-for-device', 'shell', 'getprop', 'ro.build.version.sdk')
        sdk = int(out.strip())
        if sdk < 26:
            getp = self.raw_cmd('wait-for-device', 'shell', 'dumpsys', 'activity', '|grep', 'mFocusedActivity')
        else:
            getp = self.raw_cmd('wait-for-device', 'shell', 'dumpsys', 'activity', '|grep', 'mResumedActivity')
        # out = self.raw_cmd('wait-for-device', 'shell', 'ps', '|grep', 'minicap')
        start = getp.find("com")
        end = getp.find('/')
        package = getp[start:end].strip()  # "com.android.settings"
        endactivty = getp[start:].strip()  # "com.android.setings/.abcdef xyszn"
        endactivty1 = endactivty.find(" ")  #
        aend = endactivty[:endactivty1].strip("\r\n")  # "com.android.setings/.abcdef"

        if "/." in aend:
            activity = aend.replace("/.", "/" + package + ".")
        return activity

    def setup_arg_parser(self):
        usage = "usage: %prog -c TEST_CAMPAIGN [OPTIONS]"
        parser = OptionParser(usage=usage)
        mandatory_group = OptionGroup(parser, "MANDATORIES")

        mandatory_group.add_option("-c",
                                   metavar=u"fps或者start启动时间",
                                   default="fps",
                                   dest="campaign_name")
        parser.add_option_group(mandatory_group)
        optional_group = OptionGroup(parser, "OPTIONS")
        optional_group.add_option("-s",
                                  metavar=u"123456 |设备号,只有1个设备时无需设置|",
                                  default="",
                                  dest="serial_number")

        optional_group.add_option("-p",
                                  metavar=u"com.android.settings |测试包名,默认当前窗口|",
                                  default="",
                                  dest="test_package")

        optional_group.add_option("-t",
                                  metavar=u"5 |截图时间默认3秒|",
                                  default="3",
                                  dest="screen_save")

        optional_group.add_option("-x",
                                  metavar=u"200x300 |点击点xy坐标|",
                                  default="",
                                  dest="screen_xy")

        optional_group.add_option("-a",
                                  metavar=u"com.android.settings/com.android.settings.Settings  |包名全称|",
                                  default="",
                                  dest="pkg_activity")

        optional_group.add_option("-d",
                                  metavar=u"v |滑动方向,h 水平 v 垂直 m 手动 默认v r 录制 p 回放|",
                                  default="v",
                                  dest="scrool_xy")

        optional_group.add_option("-u",
                                  metavar=u"图形界面",
                                  default="n",
                                  dest="gfxtest_gui")

        optional_group.add_option("-r",
                                  metavar=u"y |流畅度整机测试,默认n|",
                                  default="n",
                                  dest="platfrom_fps")

        optional_group.add_option("-g",
                                  metavar=u"g |不测FPS，用于提高其他测试的性能|",
                                  default="y",
                                  dest="enable_fps")

        parser.add_option_group(optional_group)
        return parser

    def raw_cmd1(self, *args):
        try:
            timeout = 15
            Returncode = "over"
            cmds = ['adb'] + ['-s'] + [self.serial] + list(args)
            p = subprocess.Popen(cmds, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            c = p.communicate()[0]
            return c
        except Exception, e:
            pass

    def raw_cmd(self, *args):
        cmds = ['adb'] + ['-s'] + [self.serial] + list(args)
        proc = subprocess.Popen(cmds, bufsize=0, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        poll_seconds = .250
        deadline = time.time() + 10
        while time.time() < deadline and proc.poll() == None:
            time.sleep(poll_seconds)
        if proc.poll() == None:
            if float(sys.version[:3]) >= 2.6:
                proc.terminate()
        stdout = proc.communicate()[0]
        return stdout


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
                if self.options.serial_number == "":
                    print u"发现多个设备，请使用 -s xxx 参数指定xxx设备序列号！"
                    sys.exit(1)
                else:
                    self.serial = self.options.serial_number
                return self.serial
        except Exception, e:
            self.textout.insert(END, "设备没找到\n")
            self.textout.update()
            sys.exit(1)

    def getAdb2(self):
        try:
            serial = []
            p = Popen("adb devices", shell=True, stdout=PIPE, stderr=PIPE)
            out = p.stdout.readlines()
            for i in range(len(out)):
                if "List" in out[i]:
                    continue
                if len(out[i]) > 5:
                    serial.append(out[i].split()[0])
            return serial
        except Exception, e:
            self.textout.insert(END, "设备没找到\n")
            self.textout.update()
            sys.exit(1)

    def monkeythread(self):
        try:
            self.killmonkey()
            self.raw_cmd('wait-for-device', 'shell', 'monkey', '-p', str(self.package),
                         '--pct-touch 40 --pct-motion 30 --pct-pinchzoom 30', '--throttle', '1000', '-s', '1',
                         '--ignore-security-exceptions',
                         '--ignore-crashes', '--ignore-timeouts', '--ignore-native-crashes', '-v', '100',
                         '>/dev/null')
        except Exception, e:
            return False

    def removeFileInFirstDir(self, targetDir):
        for file in os.listdir(targetDir):
            targetFile = os.path.join(targetDir, file)
            if os.path.isfile(targetFile):
                os.remove(targetFile)

    def swiptDown(self):
        self.shell_cmd(
            'input swipe ' + str(self.WIDTH / 2) + " " + str(self.HEIGHT * 0.7) + " " + str(self.WIDTH / 2) + " " + str(
                self.HEIGHT * 0.2))
        # self.shell_cmd(
        #     'input swipe ' + str(self.WIDTH / 2) + " " + str(self.HEIGHT * 0.7) + " " + str(self.WIDTH / 2) + " " + str(
        #         self.HEIGHT * 0.2))

    def swiptUp(self):
        self.shell_cmd(
            'input swipe ' + str(self.WIDTH / 2) + " " + str(self.HEIGHT * 0.2) + " " + str(self.WIDTH / 2) + " " + str(
                self.HEIGHT * 0.7))
        # self.shell_cmd(
        #     'input swipe ' + str(self.WIDTH / 2) + " " + str(self.HEIGHT * 0.2) + " " + str(self.WIDTH / 2) + " " + str(
        #         self.HEIGHT * 0.7))

    def swiptRight(self):
        self.shell_cmd(
            'input swipe ' + str(self.WIDTH - 50) + " " + str(self.HEIGHT / 2) + " 50 " + str(self.HEIGHT / 2))
        # self.shell_cmd(
        #     'input swipe ' + str(self.WIDTH - 50) + " " + str(self.HEIGHT / 2) + " 50 " + str(self.HEIGHT / 2))

    def swiptLeft(self):
        self.shell_cmd(
            'input swipe  50 ' + str(self.HEIGHT / 2) + " " + str(self.WIDTH - 50) + " " + str(self.HEIGHT / 2))
        # self.shell_cmd(
        #     'input swipe  50 ' + str(self.HEIGHT / 2) + " " + str(self.WIDTH - 50) + " " + str(self.HEIGHT / 2))

    def screenShot(self, path):
        self.raw_cmd('wait-for-device', 'shell', 'screencap', '/sdcard/tmp.png')
        time.sleep(1)
        self.raw_cmd('wait-for-device', 'pull', '/sdcard/tmp.png', str(path))
        time.sleep(1)

    def swipe2(self, dir):
        try:
            if "systemui" in self.package:
                # self.raw_cmd('wait-for-device', 'shell', 'input', 'keyevent 26')
                # self.raw_cmd('wait-for-device', 'shell', 'input', 'keyevent 26').communicate()[
                #     0]
                # self.raw_cmd('wait-for-device', 'shell', 'input', 'keyevent 82').communicate()[
                #     0]
                # self.raw_cmd('wait-for-device', 'shell', 'input', 'swipe', str(self.WIDTH / 2), str(self.HEIGHT * 0.7),
                #              str(self.WIDTH / 2), str(self.HEIGHT * 0.2))
                self.raw_cmd('wait-for-device', 'shell', 'input', 'swipe', str(self.WIDTH / 2), "1",
                             str(self.WIDTH / 2), str(self.HEIGHT * 0.7))
                self.raw_cmd('wait-for-device', 'shell', 'input', 'swipe', str(self.WIDTH - 50), str(self.HEIGHT / 2),
                             "50",
                             str(self.HEIGHT / 2))
                self.raw_cmd('wait-for-device', 'shell', 'input', 'keyevent 26')
                time.sleep(0.1)
                self.raw_cmd('wait-for-device', 'shell', 'input', 'keyevent 26')
                time.sleep(0.1)
                self.raw_cmd('wait-for-device', 'shell', 'input', 'keyevent 4')
            elif self.scroll_xy == "m":
                pass
            else:
                if dir == "vh" or dir == "hv":
                    self.swiptDown()
                    self.swiptUp()
                    self.swiptRight()
                    self.swiptLeft()
                elif dir == "v":
                    self.swiptDown()
                    self.swiptUp()
                elif dir == "h":
                    self.swiptRight()
                    self.swiptLeft()
        finally:
            pass
            self.screenShot(os.getcwd() + "/pic/" + self.package + str(datetime.datetime.now().second) + ".png")

    def gfxclean(self):
        results = self.raw_cmd('wait-for-device', 'shell', 'dumpsys', 'gfxinfo', self.package, 'reset')

    def swipesystemui(self):
        self.raw_cmd('wait-for-device', 'shell', 'input', 'swipe', str(self.WIDTH / 2), "1",
                     str(self.WIDTH / 2), str(self.HEIGHT * 0.7))
        self.raw_cmd('wait-for-device', 'shell', 'input', 'swipe', str(self.WIDTH - 50), str(self.HEIGHT / 2),
                     "50",
                     str(self.HEIGHT / 2))
        self.raw_cmd('wait-for-device', 'shell', 'input', 'swipe', str(self.WIDTH - 50), str(self.HEIGHT / 2),
                     "50",
                     str(self.HEIGHT / 2))
        self.raw_cmd('wait-for-device', 'shell', 'input', 'keyevent 4').communicate()[
            0]

    def gfxtest(self):
        if "systemui" in self.package:
            return self.gfxtest2()
        else:
            return self.gtest(self.package)

    def gtest(self, pkg):
        try:
            my_re = re.compile(r'[A-Za-z]', re.S)
            fps = 0
            frame_count = 0
            jank_count = 0
            vsync_overtime = 0
            draw_over = 0
            render_time = []
            draw_time = []
            fps = 0
            results = self.raw_cmd('wait-for-device', 'shell', 'dumpsys', 'gfxinfo', pkg)
            pt = False
            frames = []
            for i in results.split("\r"):
                if "Draw" in i and "Process" in i and "Execute" in i:
                    pt = True
                    j = 0
                    continue
                if pt and i != "":
                    resw = re.findall(my_re, i)
                    # if (j <= 120) & (i != "") & (len(i) > 1):
                    if len(resw) == 0:
                        frames.append(i.split())
                    else:
                        pt = False

            for frame in frames:
                if len(frame) == 4:
                    try:
                        if float(frame[0]) > (16.67):  # >16.67s
                            draw_time.append('%.2f' % (float(frame[0])))
                        rt = '%.2f' % (float(frame[0]) + float(frame[1]) + float(frame[2]) + float(frame[3]))
                        render_time.append(rt)
                    except Exception, e:
                        render_time = [0]
            frame_count = len(frames)
            if len(render_time) > 1:
                for j in render_time:
                    if float(j) > 16.67:
                        jank_count += 1
                        if float(j) % 16.67 == 0:
                            vsync_overtime += int(float(j) / 16.67) - 1
                        else:
                            vsync_overtime += int(float(j) / 16.67)
                if frame_count > 0:
                    fps = int(frame_count * 60 / (frame_count + vsync_overtime))
                    draw_over = '%.2f' % (len(draw_time) / float(frame_count))
                    # print "framecount=",frame_count,"fps_ave=",self.fps_ave,"fps=",fps,"vnc=",vsync_overtime
                    # fps = self.fps_ave + fps
                    # self.fps_ave = self.fps_ave / frame_count
                    # print "Frames=", frame_count, " Jank=", jank_count, " FPS=", self.fps_ave, " Draw=",float(draw_over)*100
        finally:
            return int(frame_count), int(jank_count), int(fps), int(float(draw_over) * 100)

    def gfxtest2(self):
        try:
            fps = 0
            jank_count = 0
            results = self.raw_cmd('wait-for-device', 'shell', 'dumpsys', 'gfxinfo', self.package)
            frames = 0
            for i in results.split("\r"):
                if "Total frames rendered:" in i:
                    # frames = i.replace("ms", "").split()[1:-1]
                    frames = i.split()[3]
                elif "Janky frames:" in i:
                    # frames = i.replace("ms", "").split()[1:-1]
                    jank_count = i.split()[2]
                elif "Number Missed Vsync:" in i:
                    # frames = i.replace("ms", "").split()[1:-1]
                    mv = i.split()[3]
            fps = int((int(frames) * 60) / (int(frames) + int(mv)))
        finally:
            return int(frames), int(jank_count), int(fps), 0

    def testFPS2(self):
        # self.killsh()
        activity = self.getActivity()
        persion = self.raw_cmd('wait-for-device', 'shell', 'getprop', 'ro.internal.build.version')
        if "8.0" in persion:
            thread.start_new_thread(
                self.raw_cmd('wait-for-device', 'shell', 'sh /data/local/tmp/fps.sh -t 60 -w ' + activity + "#0",
                             stdout=subprocess.PIPE), ("Thread-1", 2,))
        else:
            thread.start_new_thread(
                self.raw_cmd('wait-for-device', 'shell', 'sh /data/local/tmp/fps.sh -t 60 -w ' + activity,
                             stdout=subprocess.PIPE), ("Thread-1", 2,))

    def testFPS(self):
        try:
            self.inidevice()
            zhixingfangshi = self.radionButton_rp_value.get()
            frame_count = 0
            jank_count = 0
            fps = 0
            total_count = 0
            draw_over = 0
            # self.raw_cmd('wait-for-device', 'shell', 'setprop', 'debug.hwui.profile', 'visual_bars',
            #              stdout=subprocess.PIPE)  # visual_bars
            # self.raw_cmd('wait-for-device', 'shell',
            #              'monkey', '-p com.android.settings -c', 'android.intent.category.LAUNCHER', '1',
            #              stdout=subprocess.PIPE )
            # time.sleep(0.2)
            # self.raw_cmd('wait-for-device', 'shell', 'input', 'keyevent', '4',
            #              stdout=subprocess.PIPE)
            self.scroll_xy = "v"
            self.scroll_direct = "v"
            if self.typeDirect.get() == 1:
                self.scroll_direct = "h"
            if zhixingfangshi == "m":
                self.scroll_xy = "m"
            if zhixingfangshi == "s":
                self.scroll_xy = "pa"
            if zhixingfangshi == "p":
                self.scroll_xy = "p"
            x = self.startX.get()
            y = self.startY.get()
            xy = str(x + "x" + y)
            if x != "" and y != "":
                self.raw_cmd('wait-for-device', 'shell', ' input', 'tap', str(x),
                             str(y))
                # self.d.click(int(self.xy.split("x")[0]), int(self.xy.split("x")[1]))
                time.sleep(2)

            package_Edit = self.packageEdit.get()
            if package_Edit == "":
                self.package = self.getPackage()
            else:
                self.package = package_Edit
            # self.apkversion = self.getAPKVersion()

            self.textout.delete(1.0, END)
            if (self.scroll_xy == "v") and (self.scroll_direct == "h"):
                self.textout.insert(END, "FPS水平滑动" + "...\n")
            elif (self.scroll_xy == "v") and (self.scroll_direct == "v"):
                self.textout.insert(END, "FPS垂直滑动" + "...\n")
            elif self.scroll_xy == "m":
                self.textout.insert(END, "FPS手动执行" + "...\n")
            elif self.scroll_xy == "s":
                self.textout.insert(END, "FPS脚本控制" + "...\n")
            elif self.scroll_xy == "r":
                self.textout.insert(END, "录制方式" + "...\n")
            elif self.scroll_xy == "p":
                self.textout.insert(END, "FPS回放" + "...\n")
            self.textout.insert(END, "系统：" + self.buildversion + "\n")
            self.textout.insert(END, "包名：" + self.package + " 版本：" + self.apkversion + "\n")
            self.textout.insert(END, "-" * 79 + "\n")
            self.textout.update()

            if self.scroll_xy == "m" or self.scroll_xy == "p" or self.scroll_xy == "pa":
                if self.scroll_xy == "p":
                    ref = self.fileEdit.get()
                    if ref == "":
                        ref = "temp.txt"

                    for i in xrange(1, int(self.screensave) + 1):
                        results = self.raw_cmd('wait-for-device', 'shell', 'dumpsys', 'gfxinfo', self.package, 'reset')
                        self.textout.insert(END, "播放次数:" + str(i) + ", 文件:" + str(ref) + "\n")
                        self.textout.update()
                        self.replay(ref)
                        result = self.gfxtest()
                        if (result[0] > 10) & (result[2] > 0):
                            total_count = total_count + 1
                            frame_count = frame_count + result[0]
                            jank_count = jank_count + result[1]
                            fps = int(fps + result[2])
                            draw_over = (draw_over + result[3])
                            print u"第" + str(i) + u"次帧速FPS: " + str(result[2]) + u" 绿色帧：" + str(
                                result[3]) + "%" + u" 总帧数: " + str(result[0]) + u", 丢帧数: " + str(result[1])
                            self.textout.insert(END,
                                                "<" + str(i) + "> FPS=" + str(result[2]) + ", Draw=" + str(
                                                    result[3]) + "%,Total=" + str(
                                                    result[0]) + ",Janks=" + str(result[1]) + "\n")
                        else:
                            self.textout.insert(END, "滑动太少，没有足够的数据！\n")
                        self.imagetk()
                        self.textout.update()
                    # self.getLog(self.package)
                    self.screenShot(os.getcwd() + "/pic/" + self.package + str(datetime.datetime.now().second) + ".png")
                elif self.scroll_xy == "pa":
                    getfile = self.fileEdit.get()
                    (path, shotname) = os.path.split(getfile)
                    if not os.path.isfile(getfile):
                        self.textout.insert(END, "没有输入或找不到文件:" + getfile + "\n")
                        self.textout.update()
                        return 0
                    for i in xrange(1, int(self.screensave) + 1):
                        results = self.raw_cmd('wait-for-device', 'shell', 'dumpsys', 'gfxinfo', self.package, 'reset')
                        print u"播放第%i 次中..." % i
                        xy = self.playatx(getfile, self.d, self.dm)
                        self.imagetk()
                        self.textout.insert(END, "播放次数:" + str(i) + ", 文件:" + str(shotname) + ",结果：" + str(xy) + "\n")
                        self.textout.update()
                        self.screenShot(
                            os.getcwd() + "/pic/" + self.package + str(datetime.datetime.now().second) + ".png")
                elif self.scroll_xy == "m":
                    tkinter.messagebox.showinfo(title="提示框", message="现在请进入待测界面，[确认]后即进行手动滑动")
                    results = self.raw_cmd('wait-for-device', 'shell', 'dumpsys', 'gfxinfo', self.package, 'reset')
                    time.sleep(int(self.screensave))
                    total_count = 1
                    if package_Edit == "":
                        self.package = self.getPackage()
                    else:
                        self.package = package_Edit
                    #
                    # self.textout.insert(END, "系统：" + self.buildversion + "\n")
                    # self.textout.insert(END, "包名：" + self.package + " 版本：" + self.apkversion + "\n")
                    # self.textout.insert(END, "-" * 79 + "\n")
                    # self.textout.update()
                    result = self.gfxtest()

                    if (result[0] > 20) & (result[2] >= 0):
                        frame_count = frame_count + result[0]
                        jank_count = jank_count + result[1]
                        fps = int(fps + result[2])
                        draw_over = (draw_over + result[3])
                        self.textout.insert(END, "<" + str(total_count) + "> FPS=" + str(result[2]) + " Draw=" + str(
                            result[3]) + "%,Total=" + str(
                            result[0]) + ",Janks=" + str(result[1]) + "\n")
                    else:
                        self.textout.insert(END, "滑动太少，没有足够的数据！\n")
                    self.imagetk()
                    self.textout.update()
                    self.screenShot(os.getcwd() + "/pic/" + self.package + str(datetime.datetime.now().second) + ".png")
            else:

                # # print u"<请打开选项:Settings/Developer/Profile GPU rendering->ON SCREEN AS BARS;并重新启动被测试应用>"
                # self.raw_cmd('wait-for-device', 'shell', 'setprop', 'debug.hwui.profile', 'visual_bars')  # visual_bars
                # self.raw_cmd('wait-for-device', 'shell',
                #              'monkey', '-p com.android.settings -c', 'android.intent.category.LAUNCHER', '1')
                # time.sleep(0.2)
                # self.raw_cmd('wait-for-device', 'shell', 'input', 'keyevent', '4')
                # time.sleep(0.2)
                for m in xrange(0, int(self.screensave)):
                    results = self.raw_cmd('wait-for-device', 'shell', 'dumpsys', 'gfxinfo', self.package, 'reset')
                    self.swipe2(self.scroll_direct)
                    result = self.gfxtest()
                    if (result[0] < 30):
                        self.swipe2(self.scroll_direct)
                        self.swipe2(self.scroll_direct)
                        result = self.gfxtest()
                    elif (result[2] >= 0):
                        total_count = total_count + 1
                        frame_count = frame_count + result[0]
                        jank_count = jank_count + result[1]
                        fps = fps + result[2]
                        draw_over = draw_over + result[3]

                        # print u"第", total_count, u"次:", result[2], u" 绿色帧：" + str(result[3]) + u"%, 总帧数: " + str(
                        #     result[0]) + u", 丢帧数: " + str(result[1])
                        self.textout.insert(END, "<" + str(total_count) + "> FPS=" + str(result[2]) + " Draw=" + str(
                            result[3]) + "%,Total=" + str(
                            result[0]) + ",Janks=" + str(result[1]) + "\n")
                    else:
                        self.textout.insert(END, "滑动太少，没有足够的数据！\n")
                    self.imagetk()
                    self.textout.update()

                self.screenShot(os.getcwd() + "/pic/" + self.package + str(datetime.datetime.now().second) + ".png")

            if (total_count > 0) & (frame_count > 30):
                fps = fps / total_count
                draw_over = int((draw_over / total_count) / 0.75)
                # print "-" * 62
                # print str(total_count) + u" 次平均帧速:" + str(fps), u" 绿色帧:" + str(draw_over) + "%", u"; 总帧数:" + str(
                #     frame_count) + u",丢帧数: " + str(jank_count) + u",丢帧率:" + str(
                #     int((float(jank_count) / frame_count * 100))) + " %"
                # print "-" * 62
                self.textout.insert(END, "-" * 79 + "\n")
                self.textout.insert(END, str(total_count) + u" 次平均帧速: " + str(fps), u" 绿色帧: " + str(draw_over) + "%",
                                    u"; 总帧数: " + str(
                                        frame_count) + u", 丢帧数: " + str(jank_count) + u", 丢帧率: " + str(
                                        int((float(jank_count) / frame_count * 100))) + "% \n")
                self.textout.update()
            else:
                print "No enough Framers!"
                self.textout.insert(END, "滑动太少，没有足够的数据！\n")
                self.textout.update()
        except Exception, e:
            import traceback
            traceback.print_exc()
            self.textout.insert(END, "出错了\n")
            self.textout.update()
        finally:
            # self.getLog(self.package)
            self.textout.insert(END, "-" * 79 + "\n")
            self.textout.insert(END, "测试完成\n")
            self.textout.update()
            return fps, draw_over

    def killmonkey(self):
        get = True
        while get:
            ps = Popen("adb  -s " + self.serial + " shell ps | find \"monkey\"", shell=True, stdout=PIPE, stderr=PIPE)
            ps_line = ps.stdout.readline()
            ps.communicate()
            if len(ps_line) > 10:
                pl = ' '.join(filter(lambda ps_line: ps_line, ps_line.split(' ')))
                pid = pl.split(" ")[1]
                ps = Popen("adb  -s " + self.serial + " shell kill " + pid, shell=True, stdout=PIPE, stderr=PIPE)
                ps.communicate()
            else:
                get = False

    def testLaunch(self):
        try:
            self.textout.delete(1.0, END)
            self.textout.insert("1.0", "Test Minicap Start!\n")
            self.textout.update()
            if self.serial == "":
                self.serial = self.radionButton_value.get()
            self.screensave = int(self.numberChosen.get())
            if self.screensave < 3:
                self.screensave = 3
            x = self.startX.get()
            y = self.startY.get()
            xy = str(x + "x" + y)
            if x == '' or y == '':
                self.textout.insert("2.0", "Please input click point!\n")
                self.textout.update()
                return
            self.textout.insert("3.0", "Click Point: " + xy + " , please wait...\n")
            self.textout.update()
            appdev = MinicapMin.TestDevice(serial=self.serial)
            appstarttime = appdev.testAppStartTime(int(self.screensave), xy)
        except Exception, e:
            self.textout.insert(END, "出错了\n")
            self.textout.update()
            # import traceback
            # traceback.print_exc()
        finally:
            self.textout.insert("5.0", "Test Minicap End!\n ")
            self.textout.update()

    def gettest(self):
        # print "*" * 64
        # print "* %-50s *" % ("Tinno Performance Test Tool 3.3.0").center(60)
        # print "* %-50s *" % ("SERIAL:" + (self.serial)).center(60)
        # # print "* %-50s *" % ("PACKAGE:" + (self.package).upper() + "_" + self.apkversion[0:10]).center(60)
        # print "* %-50s *" % ("Example:").center(60)
        # print "* %-60s *" % ("FPS test: gfxtest.exe")
        # print "* %-60s *" % ("FPS test direction left and right: gfxtest.exe -d h")
        # print "* %-60s *" % ("Start time and click 500x600: gfxtest -c start -x 500x600")
        # print "* %-60s *" % ("SimpleRecord 10s: gfxtest -d r -t 10")
        # print "* %-60s *" % ("SimplePlay 10 times: gfxtest -d p -t 10")
        # print "* %-60s *" % ("Record to file: gfxtest -d ra")
        # print "* %-60s *" % ("Play file: gfxtest -d pa")
        # print "*" * 64
        self.screensave = int(self.numberChosen.get())
        zhixingfangshi = self.radionButton_rp_value.get()
        # serial = self.getAdb2()
        # if len(serial) == 1:
        #     self.serial = serial[0]
        # elif len(serial) > 1:
        #     self.serial = self.radionButton_value.get()
        # else:
        #     print "No any device!"
        #     self.textout.insert("1.0", "No any device found!\n")
        #     self.textout.update()
        #     return 0

        if (zhixingfangshi == "r"):
            self.record()
        # elif (zhixingfangshi == "s"):
        #     # self.recordatx()
        #     self.textout.insert(END, "目前仅支持播放，记录功能开发中！")
        #     self.textout.update()
        else:
            self.testFPS()

    def record(self):
        self.textout.delete(1.0, END)
        ref = self.fileEdit.get()
        if ref == "":
            ref = "temp.txt"
        self.textout.insert("1.0", "Record to file:" + ref)
        self.textout.update()
        cmd = "wait-for-device shell /data/local/tmp/eventrec /sdcard/" + ref
        try:
            start = datetime.datetime.now()
            process = subprocess.Popen(['adb', '-s', [self.serial], [cmd]])
            while process.poll() is None:
                time.sleep(1)
                now = datetime.datetime.now()
                if (now - start).seconds > int(self.screensave):
                    os.kill(process.pid, signal.SIGTERM)
                    return None
        except KeyboardInterrupt:
            print "Stop:", ref
        finally:
            self.raw_cmd('wait-for-device', 'pull', '/sdcard/' + ref, os.getcwd())  # visual_bars
            self.textout.delete(1.0, END)
            self.textout.insert("1.0", "Save to File:" + ref)
            self.textout.update()

    def replay(self, pf):
        start = datetime.datetime.now()
        self.raw_cmd('wait-for-device', 'push', os.getcwd() + '/' + pf, '/sdcard/')
        cmd = "wait-for-device shell /data/local/tmp/eventrec -p /sdcard/" + pf
        process = subprocess.Popen(['adb', '-s', [self.serial], [cmd]])

        while process.poll() is None:
            time.sleep(1)
            now = datetime.datetime.now()
            du = now - start
            if (du).seconds > 600:
                try:
                    process.terminate()
                    return True
                except Exception, e:
                    self.textout.insert(END, "出错了\n")
                    self.textout.update()
                    return False

    def grantPermission(self, pkg):
        "dumpsys package com.ape.filemanager | grep granted=false"
        self.raw_cmd('wait-for-device', 'shell', 'pm', 'grant', pkg,
                     "android.permission.ACCESS_COARSE_LOCATION")
        self.raw_cmd('wait-for-device', 'shell', 'pm', 'grant', pkg,
                     "android.permission.READ_EXTERNAL_STORAGE")
        self.raw_cmd('wait-for-device', 'shell', 'pm', 'grant', pkg,
                     "android.permission.WRITE_EXTERNAL_STORAGE")
        out = self.raw_cmd('wait-for-device', 'shell', 'pm', 'grant', pkg,
                           "android.permission.READ_CONTACTS")
        self.raw_cmd('wait-for-device', 'shell', 'pm', 'grant', pkg,
                     "android.permission.WRITE_CONTACTS")
        self.raw_cmd('wait-for-device', 'shell', 'pm', 'grant', pkg,
                     "android.permission.CALL_PHONE")
        self.raw_cmd('wait-for-device', 'shell', 'pm', 'grant', pkg,
                     "android.permission.RECORD_AUDIO")
        self.raw_cmd('wait-for-device', 'shell', 'pm', 'grant', pkg,
                     "android.permission.READ_PHONE_STATE")

        time.sleep(1)
        out = \
            self.raw_cmd('wait-for-device', 'shell', 'dumpsys', 'package', pkg,
                         '| grep granted=false |cut -d \':\' -f 1')
        if "permission" in out:
            b = out.strip().split("\r")
            print b
            for i in b:
                self.raw_cmd('wait-for-device', 'shell', 'pm', 'grant', pkg, i)

    def calcufps(self, pkg):
        fps = 0
        result = self.gtest(pkg)
        if (result[0] > 0) & (result[2] > 0):
            fps = result[2]
        return fps

    def platformRun2(self):
        import ConfigParser
        import glob
        import csv
        self.inidevice()
        self.textout.delete(1.0, END)
        self.textout.insert(END, "GO is runing...\n")
        self.textout.insert(END, "系统：" + self.buildversion + "\n")
        self.textout.insert(END, "-" * 79 + "\n")
        self.textout.update()

        persistentmem = 0

        persistent = self.raw_cmd('wait-for-device', 'shell', 'dumpsys', 'meminfo', '| grep -A 10 Persistent ')
        # persistentmem = self.raw_cmd('wait-for-device', 'shell', 'dumpsys', 'meminfo','| grep Persistent |cut -d \':\' -f 1',
        #                    stdout=subprocess.PIPE )
        if "Persistent" in persistent:
            persistentmem = persistent.split(":")[0]
            if "K" in persistentmem:
                persistentmem = persistentmem.replace("K", "")
            if "," in persistentmem:
                persistentmem = persistentmem.replace(",", "")
                persistentmem = int(persistentmem) / 1024
        print "" + persistent
        memAv = self.raw_cmd('wait-for-device', 'shell', 'cat', '/proc/meminfo', '|grep MemAvailable')
        if "kB" in memAv:
            memAv = int(memAv.split(":")[1].strip().replace("kB", "").strip()) / 1024
        print "Persistent:" + str(persistentmem) + " MB"
        print "MemAvailable:" + str(memAv) + " MB"

        self.textout.insert(END, "Persistent:" + str(persistentmem) + " MB" + "\n")
        self.textout.insert(END, "MemAvailable:" + str(memAv) + " MB" + "\n")
        self.textout.update()
        configl_files = []
        self.screensave = int(self.numberChosen.get())
        try:
            dsvf = "per_" + self.serial + "_" + str(datetime.datetime.now().hour) + "_" + str(
                datetime.datetime.now().minute) + "_" + str(datetime.datetime.now().second) + ".csv"
            with open(dsvf, 'ab+') as f:
                writer = csv.writer(f)
                writer.writerow(["Persistent", str(persistentmem), "MemAvailable", str(memAv) + " MB", "BuildVersion:",
                                 self.buildversion])
                writer.writerow(["package", "version", "starttime", "fps"])

            if self.fileEdit.get() != "":
                configl_files = []
                configl_files = glob.glob(self.fileEdit.get())
            else:
                configl_files = glob.glob(os.getcwd() + '/lib/res/test_app/*.config')
            for filename in configl_files:
                starttime = []
                fps = []
                fps_avg = 0
                starttime_avg = 0
                cf = ConfigParser.ConfigParser()
                cf.read(filename)
                pkg = cf.get("package", "package")
                acv = cf.get("package", "activity")
                self.package = pkg
                version, buildversion = self.getAPKVersion()
                self.grantPermission(pkg)

                try:
                    for i in xrange(1, int(self.screensave) + 1):
                        print filename, u" 执行 %i 次..." % i
                        self.raw_cmd('wait-for-device', 'shell', 'input', 'keyevent', '4')
                        time.sleep(0.1)
                        self.raw_cmd('wait-for-device', 'shell', 'input', 'keyevent', '4')
                        time.sleep(0.1)
                        self.raw_cmd('wait-for-device', 'shell', 'input', 'keyevent', '3')
                        time.sleep(0.1)
                        (path, shotname) = os.path.split(filename)
                        self.textout.insert(END, "<" + str(i) + "> 执行文件:" + str(shotname) + "\n")
                        self.textout.update()
                        out = self.raw_cmd('wait-for-device', 'shell', 'am', 'start  -S -W', pkg + '/' + acv,
                                           '|grep TotalTime|cut -d \':\' -f 2')
                        time.sleep(0.2)
                        out = out.strip()
                        if out.isdigit():
                            starttime.append(int(out))

                        try:
                            come_in = cf.get("package", "goto")
                            if come_in != "":
                                if "," in come_in:
                                    come_for = come_in.split(",")
                                    for cl in xrange(len(come_for)):
                                        if "x" in come_for[cl]:
                                            self.raw_cmd('wait-for-device', 'shell', ' input', 'tap',
                                                         str(int(come_for[cl].split("x")[0])),
                                                         str(int(come_for[cl].split("x")[1])))
                                            time.sleep(0.3)
                                else:
                                    if "/" in come_in:
                                        come_for = come_in.split("/")
                                        for cl in xrange(len(come_for)):
                                            come_for = come_in.split("/")
                                            self.d(text=come_for[cl]).click()
                                            time.sleep(1)
                                    else:
                                        self.d(text=come_in).click()
                                        time.sleep(1)
                        except Exception, e:
                            print "no goto section"

                        self.gfxclean()

                        if "ystemui" in pkg:
                            self.swipesystemui()
                        elif "etting" in pkg:
                            self.swiptDown()
                            self.swiptUp()
                            fps.append(self.calcufps(pkg))
                        elif "ialer" in pkg:
                            self.swiptDown()
                            self.swiptUp()
                            fps.append(self.calcufps(pkg))
                        elif "alculator" in pkg:
                            self.swiptUp()
                            self.swiptDown()
                            fps.append(self.calcufps(pkg))
                        else:
                            self.swiptDown()
                            self.swiptUp()
                            fps.append(self.calcufps(pkg))

                        print u"第" + str(i) + u"次<" + pkg + ">" + u"帧速FPS: " + str(fps_avg) + u" 启动时间：" + str(
                            starttime_avg)

                        self.raw_cmd('wait-for-device', 'shell', 'input', 'keyevent', '4')
                        time.sleep(0.1)
                        self.raw_cmd('wait-for-device', 'shell', 'input', 'keyevent', '4')
                        time.sleep(0.1)
                        self.raw_cmd('wait-for-device', 'shell', 'input', 'keyevent', '3')
                        time.sleep(0.1)
                    if len(starttime) >= 3:
                        starttime.remove(max(starttime))
                        starttime.remove(min(starttime))
                        starttime_avg = sum(starttime) / len(starttime)
                    else:
                        starttime_avg = sum(starttime) / len(starttime)
                    if len(fps) >= 3:
                        fps.remove(max(fps))
                        fps.remove(min(fps))
                        fps_avg = sum(fps) / len(fps)
                    else:
                        fps_avg = sum(fps) / len(fps)
                    if "." in pkg:
                        self.textout.insert(END, "<" + pkg.split(".")[-1] + ">" + ": FPS = " + str(
                        fps_avg) + ", StartTime = " + str(starttime_avg) + "\n")
                    else:
                        self.textout.insert(END, "<" + pkg + ">" + ": FPS = " + str(
                            fps_avg) + ", StartTime = " + str(starttime_avg) + "\n")
                    self.textout.insert(END, "-" * 79 + "\n")
                    self.textout.update()
                    with open(dsvf, 'ab+') as f:
                        writer = csv.writer(f)
                        writer.writerow([pkg, version, starttime_avg, fps_avg])
                except Exception, e:
                    # import traceback
                    # traceback.print_exc()
                    self.textout.insert(END, "platformRun2.LOOP()出错了\n")
                    self.textout.update()
                finally:
                    self.raw_cmd('wait-for-device', 'shell', 'am', 'force-stop', pkg)
                    # self.getLog(pkg)
        except Exception, e:
            self.textout.insert(END, "platformRun2()出错了\n")
            self.textout.update()
            # import traceback
            # traceback.print_exc()
        finally:
            self.textout.insert(END, "-" * 79 + "\n")
            self.textout.insert(END, "测试完成\n")
            self.textout.update()

    def platformRun3(self):
        import ConfigParser
        import csv
        cf = ConfigParser.ConfigParser()
        try:
            dsvf = "per_" + str(datetime.datetime.now().hour) + "_" + str(datetime.datetime.now().second) + ".csv"
            with open(dsvf, 'ab+') as f:
                writer = csv.writer(f)
                writer.writerow(["package", "version", "starttime", "fps"])
                out = \
                    self.raw_cmd('wait-for-device', 'shell', 'pm list package ').communicate()[
                        0]

            pkg = ""
            for k in (out.strip().split("\r")):
                starttime = []
                starttime_avg = 0
                fps = []
                fps_avg = 0
                version = ""
                pkg = k[k.find("com"):]
                self.package = pkg
                lout = \
                    self.raw_cmd('wait-for-device', 'shell',
                                 'dumpsys package ' + pkg + "|grep android.intent.category.LAUNCHER")
                if not "android.intent.category.LAUNCHER" in lout:
                    continue
                version = self.getAPKVersion()
                if "com.android" in pkg or "com.ape" in pkg or "com.myos" in pkg:
                    for i in xrange(1, int(self.screensave) + 1):
                        print  u" 执行 %i 次..." % i
                        self.raw_cmd('wait-for-device', 'shell', 'am', 'force-stop', pkg)
                        time.sleep(2)
                        out = self.raw_cmd('wait-for-device', 'shell', 'am', 'start -W', pkg,
                                           '|grep TotalTime|cut -d \':\' -f 2')
                        time.sleep(1)
                        out = out.strip()
                        self.swipe12()
                        result = self.gtest(pkg)
                        if (result[0] != 0) & (result[2] != 0):
                            fps.append(result[2])
                            if len(fps) > 3:
                                fps.remove(max(fps))
                                fps.remove(min(fps))
                            fps_avg = sum(fps) / len(fps)
                        if out.isdigit():
                            starttime.append(int(out))
                            if len(starttime) > 3:
                                starttime.remove(max(starttime))
                                starttime.remove(min(starttime))
                            starttime_avg = sum(starttime) / len(starttime)
                        self.raw_cmd('wait-for-device', 'shell', 'am', 'force-stop', pkg)
                        print u"第" + str(i) + u"次<" + pkg + ">" + u"帧速FPS: " + str(fps_avg) + u" 启动时间：" + str(
                            starttime_avg)
                    with open(dsvf, 'ab+') as f:
                        writer = csv.writer(f)
                        writer.writerow([pkg, version, starttime_avg, fps_avg])
        except Exception, e:
            import traceback
            traceback.print_exc()
            self.textout.insert(END, "出错了\n")
            self.textout.update()

    def killsh(self):
        ps_line = self.raw_cmd('wait-for-device', 'shell', 'cat', '/data/local/tmp/FPS.pid')
        if len(ps_line) > 0:
            pid = ps_line.strip()
            self.raw_cmd('wait-for-device', 'shell', 'kill', str(pid))
        time.sleep(1)

    def get_battery(self):
        output = self.raw_cmd('wait-for-device', 'shell', 'dumpsys battery')
        battery2 = int(re.findall("level:.(\d+)*", output, re.S)[0])
        print battery2

    def get_cpuT(self):
        cpu = 0
        mem = 0
        try:
            d = threading.Thread(target=self.cpuThreading)
            d.setDaemon(True)
            d.start()
        except Exception, e:
            # import traceback
            # traceback.print_exc()
            self.textout.insert(END, "出错了\n")
            self.textout.update()

    def cpuThreading(self):
        cpu = 0
        mem = 0
        try:
            while (self.cpu_flag):
                time.sleep(2)
                pkg = self.getPackage()
                cmd = "wait-for-device shell top -n 1 | grep %s" % (pkg[:13])
                process = subprocess.Popen(['adb', '-s', [self.serial], [cmd]], stdout=PIPE, stderr=PIPE)
                output = process.stdout.readline()
                mem = int(float(self.getMemInfo(pkg)))
                if pkg[:13] in output:
                    sdkout = self.raw_cmd('wait-for-device', 'shell', 'getprop', 'ro.build.version.sdk')
                    sdk = int(sdkout.strip())
                    if sdk < 26:
                        cpu = int(float((output[output.find("%") - 2:output.find("%")]).strip()))
                    else:
                        cpu = int(float((output[output.find("S") + 1:output.find("S") + 7]).strip()))
                # print pkg, cpu, mem
                self.q.put([pkg, {"cpu": cpu, "mem": mem}])
                # print pkg + "[ CPU: " + str((cpu)) + "%, Memory:" + str(int(float(self.mem))), "M ]"
        except Exception, e:
            # import traceback
            # traceback.print_exc()
            self.textout.insert(END, "出错了\n")
            self.textout.update()
        finally:
            return mem, cpu

    def getMemInfo(self, pkg):
        try:
            memJava = []
            memSystem = []
            memPrivate = []
            memTotal3 = []
            memJava3 = []
            memNative3 = []
            memNative = []
            memGraphics = []
            memTotal = []
            memCode = []
            memStack = []
            getmemory = "adb -s " + self.serial + " shell \"dumpsys meminfo --package " + pkg + " | grep -A 55 \\[" + \
                        pkg + "\\] | grep -E '(TOTAL:)|(Java Heap:)|(Native Heap:)|(Code:)|(Stack:)|(Graphics:)|(Private Other:)|(System:)'\""
            pm = Popen(getmemory, shell=True, stdout=PIPE, stderr=PIPE)
            readlins = pm.stdout.readlines()
            if len(readlins) >= 7:
                readlin = readlins[-8:]
                for i in xrange(0, len(readlin)):
                    if "Java Heap" in readlin[i]:
                        javaheap = readlin[i].split(":")[1].strip(" ").strip("\r\n")
                        javaheap = round(int(re.findall(r'\d+', javaheap)[0]) / 1024.0, 2)
                        memJava.append(javaheap)
                    elif "Native Heap" in readlin[i]:
                        nativeheap = readlin[i].split(":")[1].strip(" ").strip("\r\n")
                        nativeheap = round(int(re.findall(r'\d+', nativeheap)[0]) / 1024.0, 2)
                        memNative.append(nativeheap)

                    elif "TOTAL:" in readlin[i]:
                        memtotal = readlin[i].split(":")[1].strip(" ").strip("\r\n")
                        memtotal = round(int(re.findall(r'\d+', memtotal)[0]) / 1024.0, 2)
                        memTotal.append(memtotal)
                    elif "Code:" in readlin[i]:
                        code = readlin[i].split(":")[1].strip(" ").strip("\r\n")
                        code = round(int(re.findall(r'\d+', code)[0]) / 1024.0, 2)
                        memCode.append(code)

                    elif "Stack:" in readlin[i]:
                        stack = readlin[i].split(":")[1].strip(" ").strip("\r\n")
                        stack = round(int(re.findall(r'\d+', stack)[0]) / 1024.0, 2)
                        memStack.append(stack)

                    elif "Graphics:" in readlin[i]:
                        graphics = readlin[i].split(":")[1].strip(" ").strip("\r\n")
                        graphics = round(int(re.findall(r'\d+', graphics)[0]) / 1024.0, 2)
                        memGraphics.append(graphics)

                    elif "Private:" in readlin[i]:
                        private = readlin[i].split(":")[1].strip(" ").strip("\r\n")
                        private = round(int(re.findall(r'\d+', private)[0]) / 1024.0, 2)
                        memPrivate.append(private)

                    elif "System:" in readlin[i]:
                        system = readlin[i].split(":")[1].strip(" ").strip("\r\n")
                        system = round(int(re.findall(r'\d+', system)[0]) / 1024.0, 2)
                        memSystem.append(system)

                if len(memTotal) > 0:
                    m = memTotal
                    x = [float(m) for m in m if m]
                    av = 0
                    if len(x) > 0:
                        memTotal3.append(max(x))
                        memTotal3.append(min(x))
                        mt = len(x)
                        ma = sum(x)
                        av = round(ma / mt, 2)
                    memTotal3.append(av)
                if len(memJava) > 0:
                    m = memJava
                    x = [float(m) for m in m if m]
                    av = 0
                    if len(x) > 0:
                        memJava3.append(max(x))
                        memJava3.append(min(x))
                        mt = len(x)
                        ma = sum(x)
                        av = round(ma / mt, 2)
                    memJava3.append(av)

                if len(memNative) > 0:
                    m = memNative
                    x = [float(m) for m in m if m]
                    av = 0
                    if len(x) > 0:
                        memNative3.append(max(x))
                        memNative3.append(min(x))
                        mt = len(x)
                        ma = sum(x)
                        av = round(ma / mt, 2)
                    memNative3.append(av)
                    # print self.memTotal, memJava, self.memNative,memTotal3,memJava3,memNative3,self.memCode,self.memStack,self.memGraphics,memPrivate,memSystem
        except Exception, e:
            self.textout.insert(END, "getMemInfo()出错了\n")
            self.textout.update()
        finally:
            # print "mem:",memTotal3
            # return self.memTotal, memJava, self.memNative, memTotal3, memJava3, memNative3, self.memCode, self.memStack, self.memGraphics, memPrivate, memSystem
            if len(memTotal3) > 0:
                return str(memTotal3[0])
            else:
                return 0

    def tomd5(self, node):
        # act = self.getActivity()
        # t = ""
        # if len(node) > 10:
        #     nodelen = 6
        # else:
        #     nodelen = len(node)
        # for i in xrange(1, nodelen):
        #     t = str(node[i].bounds) + str(node[i].text) + t
        return hashlib.md5(str(node)).hexdigest()

    def _parse_xml_node(self, node):
        # ['bounds', 'checkable', 'class', 'text', 'resource_id', 'package']
        __alias = {
            'class': 'class_name',
            'resource-id': 'resource_id',
            'content-desc': 'content_desc',
            'long-clickable': 'long_clickable',
        }

        def parse_bounds(text):
            m = re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', text)
            if m is None:
                return None
            return Bounds(*map(int, m.groups()))

        def str2bool(v):
            return v.lower() in ("yes", "true", "t", "1")

        def convstr(v):
            return v.encode('utf-8')

        parsers = {
            'bounds': parse_bounds,
            'text': convstr,
            'class_name': convstr,
            'resource_id': convstr,
            'package': convstr,
            'checkable': str2bool,
            'scrollable': str2bool,
            'focused': str2bool,
            'clickable': str2bool,
            'enabled': str2bool,
            'selected': str2bool,
            'long_clickable': str2bool,
            'focusable': str2bool,
            'password': str2bool,
            'index': int,
            'content_desc': convstr,
        }
        ks = {}
        for key, value in node.attributes.items():
            key = __alias.get(key, key)
            f = parsers.get(key)
            if value is None:
                ks[key] = None
            elif f:
                ks[key] = f(value)
        for key in parsers.keys():
            ks[key] = ks.get(key)
        ks['xml'] = node

        return UINode(**ks)

    def dumnode(self):
        try:
            allmd5 = ""
            xy = {}
            nodehas = []
            canbeclick = ["android.widget.Button", "android.widget.TextView", "android.widget.ImageButton",
                          "android.widget.ImageView", "android.widget.CompoundButton"]
            cannotbeclick = ["USB tethering", "reset", "RESET", "Factory data reset", "Start now", "Navigate up",
                             "USB connected, check to tether"]
            out = self.raw_cmd('wait-for-device', 'shell', '/system/bin/uiautomator ', 'dump', '--compressed',
                               '/sdcard/gfxtest.xml')
            time.sleep(0.2)
            xmldata = self.raw_cmd('wait-for-device', 'shell', 'cat', '/sdcard/gfxtest.xml')
            dom = xml.dom.minidom.parseString(xmldata)
            root = dom.documentElement
            nodes = root.getElementsByTagName('node')
            ui_nodes = []
            allnode = ""

            for node in nodes:
                ui_nodes.append(self._parse_xml_node(node))
            nodecount = len(ui_nodes)
            for i in xrange(nodecount):
                if ui_nodes[i].class_name in canbeclick:
                    # if (("ALLOW" ==ui_nodes[i].text) and(ui_nodes[i].class_name=="android.widget.Button")):
                    #     self.permissionClick(ui_nodes[i].bounds.center)
                    if (ui_nodes[i].text not in cannotbeclick) & (ui_nodes[i].content_desc not in cannotbeclick):
                        clickmd5 = self.tomd5(
                            ui_nodes[i].class_name + ui_nodes[i].content_desc + ui_nodes[i].resource_id + str(
                                ui_nodes[i].bounds.center))
                        # self.blacklist.append(clickmd5)
                        # allnode = allnode + ";" + ui_nodes[i].class_name + "," + ui_nodes[i].content_desc + "," + \
                        #           ui_nodes[i].resource_id + "," + str(ui_nodes[i].bounds.center)
                        allnode = allnode + ";" + ui_nodes[i].class_name + \
                                  ui_nodes[i].resource_id + "," + str(ui_nodes[i].bounds.center)
                        xy[clickmd5] = ui_nodes[i].bounds.center
            allmd5 = self.tomd5(allnode)
            if allmd5 not in self.md5list:
                self.md5list.append(allmd5)
        except Exception, e:
            self.textout.insert(END, "出错了\n")
            self.textout.update()
        finally:
            return allmd5, xy, allnode

    def travel2(self, pkg):
        try:
            clicklist = {}
            blacklist = {}

            nomd, xy, an = self.dumnode()
            perkey = []
            runtflat = True
            while ("packageinstaller" in an) or ("android:id/alertTitle" in an):
                for p in xrange(6):
                    for pi in xy.keys():
                        perkey.append(xy.get(pi))
                self.permissionClick(max(perkey))
                nomd, xy, an = self.dumnode()

            base = xy
            nomdo = nomd
            ct = 0
            timeNow = time.time()
            packagenow = pkg
            while (ct <= int(590) and (len(xy) > 0) and runtflat):
                ct = time.time() - timeNow
                ky = xy.keys()[random.randint(0, len(xy) - 1)]
                cxy = xy.pop(ky)
                if (ky not in blacklist):
                    if (ky in clicklist):
                        clicklist[ky] = clicklist[ky] + 1
                    else:
                        clicklist[ky] = 1
                    if (clicklist[ky]) < 10:
                        self.raw_cmd('wait-for-device', 'shell', ' input', 'tap', str(cxy[0]),
                                     str(cxy[1]))
                    packagenow = self.getPackage()
                    if pkg not in packagenow:
                        blacklist[ky] = cxy
                        if pkg != "":
                            self.raw_cmd('wait-for-device', 'shell', 'am', 'force-stop', pkg)
                        self.raw_cmd('wait-for-device', 'shell', 'input', 'keyevent', '3')
                        self.raw_cmd('wait-for-device', 'shell',
                                     'monkey', '-p', pkg, '-c', 'android.intent.category.LAUNCHER', '1')
                    time.sleep(1)
                    nomdn, xy, an = self.dumnode()
                    if nomdn == nomdo:
                        blacklist[ky] = cxy
                        continue
                    else:
                        nomdo = nomdn
                inter = dict.fromkeys([x for x in base if x in blacklist])
                df = list(set(base.keys()).difference(set(inter.keys())))
                if (df == []):
                    # print  pkg + "-->over!"
                    break
                elif len(xy) == 0:
                    if pkg != "":
                        self.raw_cmd('wait-for-device', 'shell', 'am', 'force-stop', pkg)
                    time.sleep(0.2)
                    self.raw_cmd('wait-for-device', 'shell',
                                 'monkey', '-p', pkg, '-c', 'android.intent.category.LAUNCHER', '1')
                    time.sleep(1)
                    nomdn, xy, an = self.dumnode()
                    runtflat = False
                    self.raw_cmd('wait-for-device', 'shell', 'input', 'keyevent', '4')
                    self.raw_cmd('wait-for-device', 'shell', 'input', 'keyevent', '3')
                    print  pkg + "-->End!"
        except Exception, e:
            self.cpu_flag = False
            # import traceback
            # traceback.print_exc()
            self.textout.insert(END, "出错了\n")
            self.textout.update()
        finally:
            self.cpu_flag = False

    def permissionClick(self, xy):
        os.system('adb -s ' + self.serial + " wait-for-device shell input tap " + str(xy[0]) + " " + str(xy[1]))
        time.sleep(0.2)

    def coverfile(self):
        inputevent = self.getpad()
        orx = 480
        ory = 960
        nowx = self.WIDTH
        nowy = self.HEIGHT
        x = 0
        y = 0
        with open('a.txt', 'a+') as f:
            lines = f.read()
        with open('b.txt', 'w') as f:
            for line in lines.split("\n"):
                if line != "":
                    line = line.replace(line[line.find("/dev/input"):line.find(":")], inputevent)
                    if "0035" == line.split()[4]:
                        x = line.split()[5]
                        print "ox:", x
                        x = int(str('0x' + x), 16)  # 16 to 10
                        if orx > nowx:
                            x = int(x) * orx / nowx
                        else:
                            x = int(x) * nowx / orx
                        x = hex(x)
                        x = str(x).split("0x")[1].zfill(8)
                        print "nx:", x

                        f.write(line[:-8] + x + "\n")
                    elif "0036" == line.split()[4]:
                        y = line.split()[5]
                        print "oy:", y
                        y = int(str('0x' + y), 16)  # 16 to 10
                        if ory > nowy:
                            y = int(y) * ory / nowy
                        else:
                            y = int(y) * nowy / ory
                        y = hex(y)
                        y = str(y).split("0x")[1].zfill(8)
                        print "oy:", y
                        f.write(line[:-8] + y + "\n")
                    else:
                        f.write(line + "\n")

    def getpad(self):
        try:
            out = self.raw_cmd('wait-for-device', 'shell', 'getevent -p  | grep -B 15 \"0035\"')
            outl = out.split("\n")
            inputevent = ""
            for i in xrange(len(outl)):
                if len(outl) > 0:
                    outlo = outl[-1]
                    if "/dev/input/event" in outlo:
                        inputevent = outlo[outlo.find("/dev/input"):]
                        inputevent = inputevent.strip()
                        break
                    else:
                        if len(outl) > 0:
                            outl.remove(outl[-1])
        except Exception, e:
            self.textout.insert(END, "出错了\n")
            self.textout.update()
        finally:
            return inputevent

    def recordatx(self):
        try:
            getfile = raw_input("Please input save file name: ")
            if getfile == "":
                print "Please input the record file name!"
                sys.exit(1)
            if os.path.isfile(os.getcwd() + "/" + getfile):
                os.remove(os.getcwd() + "/" + getfile)
            p = subprocess.Popen(['adb', '-s', self.serial, 'shell', 'getevent', '-l'], stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)

            self.recordmain(p.stdout, getfile)
            # while(True):
            #     print  p.stdout.readline()
            #     time.sleep(1)
        except KeyboardInterrupt:
            p.kill()
        finally:
            print "save to file!"

    def recordmain(self, pipe, filename):
        xs, ys = [], []
        lastOper = ''
        touchStart = 0
        start = time.time()
        begin = time.time()
        DEVSCREEN = self.getpad()

        def record(fmt, *args):
            outstr = fmt % args
            if filename:
                with open(filename, 'a+') as file:
                    file.write(outstr + '\n')

        record('display:' + str(self.WIDTH) + '_' + str(self.HEIGHT))
        while True:
            line = pipe.readline()
            if not line.startswith(DEVSCREEN):
                continue
            channel, event, oper, value = line.split()
            # print value#int(value, 16)
            if "DOWN" in value:
                continue
            else:
                # if oper == 'SYN_REPORT':
                #     continue
                if oper == 'ABS_MT_POSITION_X':
                    value = int(value, 16)
                    xs.append(value)
                elif oper == 'ABS_MT_POSITION_Y':
                    value = int(value, 16)
                    ys.append(value)
                elif value == 'UP' or oper == "SYN_REPORT":
                    if 1 == 1:
                        # xs = map(lambda x: x / self.WIDTH, xs)
                        # ys = map(lambda y: y / self.HEIGHT, ys)
                        if len(xs) != 0 and len(ys) != 0:  # every thing is OK
                            (x1, y1), (x2, y2) = (xs[0], ys[0]), (xs[-1], ys[-1])
                            dist = ((x2 - x1) * (x2 - x1) + (y2 - y1) * (y2 - y1)) ** 0.5

                            duration = time.time() - touchStart
                            # touch up
                            if dist < 50:
                                print "click:", x1, y1
                                record('clickscreen:%dx%d', x1, y1)
                            else:
                                print "drag:", x1, y1, x2, y2
                                record('drag:%d, %d, %d, %d,30', x1, y1, x2, y2)
                        xs, ys = [], []
                    else:
                        if len(xs) == 1:
                            # touch down
                            record('app.sleep(%.2f)', float(time.time() - start))
                            start = time.time()
                            touchStart = time.time()
                lastOper = oper

    def playatx(self, playfile, device, devicemin):
        playscreenx = self.WIDTH
        playscreeny = self.HEIGHT
        restricscreen = self.getShape()
        resx = restricscreen[0]
        resy = restricscreen[1]
        d = device
        res = "True"
        try:
            with open(playfile, 'a+') as f:
                lines = f.read()
                for line in lines.split("\n"):
                    if line != "":
                        if "display:" in line:
                            playscreenx = int(line.split(":")[1].split("_")[0])
                            playscreeny = int(line.split(":")[1].split("_")[1])
                        elif "clickscreen" in line:
                            par = line.split(":")[1]
                            x = int(par.split("x")[0])
                            y = int(par.split("x")[1])
                            # print playscreenx,playscreeny
                            if playscreenx > self.WIDTH:
                                x = int(x) * playscreenx / self.WIDTH
                            else:
                                x = int(x) * self.WIDTH / playscreenx
                            if playscreeny > self.HEIGHT:
                                y = int(y) * playscreeny / self.HEIGHT
                            else:
                                y = int(y) * self.HEIGHT / playscreeny
                            # print int(x),int(y),resx,resy
                            if int(y) > int(resy):
                                if (int(x)) < self.WIDTH / 3:
                                    d.press.back()
                                    time.sleep(1)
                                elif (int(x)) > self.WIDTH * 0.7:
                                    res = d.press.recent()
                                    time.sleep(1)
                                else:
                                    res = d.press.home()
                                    time.sleep(1)
                            else:
                                res = d.click(x, y)
                                time.sleep(1)
                        elif "drag" in line or "swipe" in line:
                            par = line.split(":")[1]
                            x = int(par.split(",")[0])
                            y = int(par.split(",")[1])
                            x1 = int(par.split(",")[2])
                            y1 = int(par.split(",")[3])

                            if playscreenx > self.WIDTH:
                                x = int(x) * playscreenx / self.WIDTH
                                x1 = int(x1) * playscreenx / self.WIDTH
                            else:
                                x = int(x) * self.WIDTH / playscreenx
                                x1 = int(x1) * self.WIDTH / playscreenx
                            if playscreeny > self.HEIGHT:
                                y = int(y) * playscreeny / self.HEIGHT
                                y1 = int(y1) * playscreeny / self.HEIGHT
                            else:
                                y = int(y) * self.HEIGHT / playscreeny
                                y1 = int(y1) * playscreeny / self.HEIGHT
                            if "drag" in line:
                                res = d.drag(x, y, x1, y1, 30)
                            else:
                                res = d.swipe(x, y, x1, y1, 30)

                        elif "checktext" in line:
                            x = line.split(":")[1]
                            p = d(text=x).wait.exists(timeout=5000)
                            if p:
                                res = "True"
                                self.textout.insert(END, "Text <" + x + ">" + " < Found!> \n")
                                self.textout.update()
                                d.screenshot(
                                    "pic/checktext_Found_" + time.strftime("%m%d%H%M%S", time.localtime()) + ".png")

                            else:
                                res = "False"
                                self.textout.insert(END, "Text <" + x + ">" + " < Not Found!>\n")
                                self.textout.update()
                                d.screenshot(
                                    "pic/checktext_NotFound_" + time.strftime("%m%d%H%M%S", time.localtime()) + ".png")

                        elif "checkimage" in line:
                            x = line.split(":")[1]
                            getORno = devicemin.wait(x, timeout=10)
                            if getORno == None:
                                res = "False"
                                self.textout.insert(END, "Image <" + x + ">" + " < Not Found! " + " >\n")
                                self.textout.update()
                                d.screenshot(
                                    "pic/checkimage_nf_" + time.strftime("%m%d%H%M%S", time.localtime()) + ".png")
                            elif getORno.matched:
                                res = "True"
                                self.textout.insert(END,
                                                    "Image <" + x + ">" + " < Found at: " + str(getORno[0]) + " >\n")
                                d.screenshot(
                                    "pic/checkimage_f_" + time.strftime("%m%d%H%M%S", time.localtime()) + ".png")

                        elif "ocrtext" in line:
                            self.screenShot(os.getcwd())
                            x = line.split(":")[1]
                            result = MYOCRTest.repara()
                            print result
                            for i in xrange(len(result)):
                                if x[1:-1] in result[i].get("words"):
                                    self.logger.info("<" + x + ">" + " < Found! >")
                                    res = "True"
                                    break
                                elif i == len(result) - 1:
                                    res = "False"
                                    self.logger.info("<" + x + ">" + " < Not Found! >")
                                    d.screenshot(
                                        "pic/ocrtext_nf_" + time.strftime("%m%d%H%M%S", time.localtime()) + ".png")

                        elif "ocrface" in line:
                            print u"人脸识别"
                            res = MYOCRTest.repface()

                        elif "sleep" in line:
                            if ":" in line:
                                x = line.split(":")[1]
                                time.sleep(int(x))
                            else:
                                time.sleep(1)
                            res = "True"

                        elif "pressback" in line:
                            res = d.press.back()

                        elif "reboot" in line:
                            self.raw_cmd('wait-for-device', 'shell', 'reboot')
                            time.sleep(30)
                            out = self.raw_cmd('wait-for-device', 'shell', 'get-state')
                            if "device" in out:
                                print "reboot ok"

                        elif "presshome" in line:
                            res = d.press.home()

                        elif "clicktext" in line:
                            x = line.split(":")[1]
                            res = d(text=x).click()

                        elif "playrecord" in line:
                            file = line.split(":")[1]
                            res = self.replay(file)

                        elif "clickimage" in line:
                            x = line.split(":")[1]
                            getORno = devicemin.wait(x, timeout=12)
                            if getORno == None:
                                res = "False"
                                # self.logger.error("<" + x + ">" + " < Not Found! >")
                                d.screenshot(
                                    "pic/imagenotfound_" + time.strftime("%m%d%H%M%S", time.localtime()) + ".png")
                            elif getORno.matched:
                                d.click(getORno[0][0], getORno[0][1])
                                time.sleep(0.2)
                                res = "True"
                                # self.logger.info("Image <" + x + ">" + " < Found at: " + str(getORno[0]) + ">")


        except Exception, e:
            # out = self.raw_cmd('wait-for-device', 'kill-server')
            # out = self.raw_cmd('wait-for-device', 'start-server')
            # print e.message
            self.textout.insert(END, "出错了\n")
            self.textout.update()
        finally:
            return res

    def getPackageAllActivitys(self, pkg):
        pkgs = []
        cmds = 'dumpsys package ' + pkg + '| grep ' + pkg + '/'
        out = self.shell_cmd(cmds)
        for i in out.split("\n"):
            j = i.split()
            if len(j) > 1:
                if "/." in j[1] or "/com" in j[1]:
                    k = j[1]
                    if "}" in k:
                        k = k.replace("}", "")
                    elif "{" in k:
                        k = k.replace("{", "")
                    if "/." in k:
                        act = pkg + k.split("/")[1]
                    else:
                        act = k.split("/")[1]
                    pkgs.append(act)
        return pkgs

    def getCurrentActivitys(self):
        out = self.shell_cmd('getprop ro.build.version.sdk')
        sdk = int(out.strip())
        if sdk < 26:
            getp = self.shell_cmd('dumpsys activity |grep mFocusedActivity')
        else:
            getp = self.shell_cmd('dumpsys activity |grep mResumedActivity')
        out = self.shell_cmd('')
        start = getp.find("com")
        end = getp.find('}')
        package = getp[start:end].strip().split()[0]  # 'com.ape.launcher/com.myos.MyosLauncher'
        activity = package.split("/")[1]  # 'com.myos.MyosLauncher'
        if "/." in package:
            activity = package.split("/")[0] + activity

        # apkversion = self.raw_cmd('wait-for-device', 'shell', 'dumpsys', "package", package, "|", "grep",'versionName', '|head -n 1')
        return activity

    def getShape(self):
        rsRE = re.compile('\s*mRestrictedScreen=\(\d+,\d+\) (?P<w>\d+)x(?P<h>\d+)')
        for line in subprocess.check_output('adb -s ' + self.serial + ' shell dumpsys window', shell=True).splitlines():
            m = rsRE.match(line)
            if m:
                return m.groups()
        raise RuntimeError('Couldn\'t find mRestrictedScreen in dumpsys')

    def shell_cmd(self, cmd):
        cmds = 'adb ' + ' -s ' + self.serial + ' wait-for-device shell ' + "\"" + cmd + "\""
        return os.popen(cmds).read()

    def travelApp(self, pkg):
        try:
            clicklist = {}
            blacklist = {}
            allActivits = self.getPackageAllActivitys(pkg)
            for p in allActivits:
                clicklist[p] = []
            perkey = []
            runtflat = True
            self.shell_cmd('am force-stop ' + pkg)
            self.shell_cmd('input keyevent 4')
            self.shell_cmd('input keyevent 4')
            self.shell_cmd('input keyevent 4')
            self.raw_cmd('wait-for-device', 'shell',
                         'monkey', '-p', pkg, '-c', 'android.intent.category.LAUNCHER', '1')

            time.sleep(1)
            nomd, xy, an = self.dumnode()
            if pkg not in self.getPackage():
                for pi in xy.keys():
                    perkey.append(xy.get(pi))
                for i in xrange(0, 6):
                    if pkg not in self.getPackage():
                        self.permissionClick(max(perkey))
            time.sleep(2)
            nomd, xy, an = self.dumnode()
            base = xy
            nomdo = nomd
            ct = 0
            timeNow = time.time()
            packagenow = pkg
            activityOld = self.getCurrentActivitys()
            while (ct <= int(590) and (len(xy) > 0) and runtflat):
                ct = time.time() - timeNow
                ky = xy.keys()[random.randint(0, len(xy) - 1)]  # point "md5":"100x200",ky is key
                cxy = xy.pop(ky)  # point "md5":"100x200",cxy is value
                os.system(
                    'adb -s ' + self.serial + " wait-for-device shell input tap " + str(cxy[0]) + " " + str(cxy[1]))
                time.sleep(0.2)
                nomdn, xy, an = self.dumnode()
                activityNow = self.getCurrentActivitys()
                if cxy not in clicklist[activityOld]:
                    clicklist[activityOld].append(ky)

                if activityNow not in allActivits:
                    clicklist[ky] = cxy
                    self.shell_cmd('input keyevent 4')
                    if self.getCurrentActivitys() not in allActivits:
                        self.shell_cmd('input keyevent 4')
                    if self.getCurrentActivitys() not in allActivits:
                        self.shell_cmd('input keyevent 4')
                    if self.getCurrentActivitys() not in allActivits:
                        self.raw_cmd('wait-for-device', 'shell',
                                     'monkey', '-p', pkg, '-c', 'android.intent.category.LAUNCHER', '1')
                else:
                    if activityOld != activityNow:  # come to new activity
                        if cxy in clicklist[activityOld]:
                            clicklist[activityOld].remove(cxy)
                        activityOld = activityNow



        except Exception, e:
            self.cpu_flag = False
            # import traceback
            # traceback.print_exc()
            self.textout.insert(END, "出错了\n")
            self.textout.update()
        finally:
            self.cpu_flag = False

    def takeshot(self):
        try:
            out = subprocess.Popen(
                ['adb', '-s', self.serial, 'shell', 'LD_LIBRARY_PATH=/data/local/tmp', '/data/local/tmp/minicap',
                 '-i', ],
                stdout=subprocess.PIPE).communicate()[0]
            m = re.search('"width": (\d+).*"height": (\d+).*"rotation": (\d+)', out, re.S)
            w, h, r = map(int, m.groups())
            w, h = min(w, h), max(w, h)
            params = '{x}x{y}@{x1}x{y1}/{r}'.format(x=w, y=h, x1=w, y1=h, r=0)
            cmd = 'shell LD_LIBRARY_PATH=/data/local/tmp /data/local/tmp/minicap -P %s' % params + ' -S -s > /sdcard/maintmp.png'
            pullcmd = 'pull /sdcard/maintmp.png ./maintmp.png'
            subprocess.Popen(['adb', '-s', self.serial, [cmd]], stdout=None).communicate()
            subprocess.Popen(['adb', '-s', self.serial, [pullcmd]], stdout=None).communicate()
            time.sleep(0.3)
        except Exception, e:
            pass

    def imagetk(self):
        try:
            self.takeshot()
            img = Image.open(os.getcwd() + '/maintmp.png')  # 打开图片
            w, h = img.size
            img = img.resize((360, 720), Image.ANTIALIAS)
            # photo = ImageTk.PhotoImage(img)  # 用PIL模块的PhotoImage打开
            # self.imglabel = Label(self.root, image=photo)
            # self.imglabel.place(x=700, y=0, width=324, height=600)

            image = img.copy()
            # image.thumbnail((360, 720), Image.ANTIALIAS)
            tkimage = ImageTk.PhotoImage(image)
            self._tkimage = tkimage  # keep a reference

            self.canvas.config(width=w, height=h)
            self.canvas.create_image(0, 0, anchor=tkinter.NW, image=tkimage)

        except Exception, e:
            pass

    def executeManu(self):
        x = self.startX.get()
        y = self.startY.get()
        xy = str(x + "x" + y)
        if x != "" and y != "":
            if ("," in x) and ("," in y):
                self.raw_cmd('wait-for-device', 'shell', 'input', 'swipe', str(x.split(",")[0]), str(x.split(",")[1]),
                             str(y.split(",")[0]), str(y.split(",")[0]))
            else:
                self.raw_cmd('wait-for-device', 'shell', ' input', 'tap', str(x), str(y))

        elif x == "back" and y == "":
            self.raw_cmd('wait-for-device', 'shell', 'input', 'keyevent', '4')
        elif x == "home" and y == "":
            self.raw_cmd('wait-for-device', 'shell', 'input', 'keyevent', '3')
        time.sleep(1)
        self.imagetk()

    def _mouse_click(self, event):
        self._moved = False
        c = self.canvas
        st = datetime.datetime.now()
        self.cavas_x_y[st] = (int(c.canvasx(event.x)), int(c.canvasy(event.y)))
        self._mouse_motion = "click"
        # click_y = cavas_x
        # click_x = cavas_y
        # if int(self.WIDTH) > 360:
        #     click_x = cavas_x * (self.WIDTH / 360)
        # else:
        #     click_x = cavas_x * (360 / self.WIDTH)
        # if int(self.HEIGHT) > 720:
        #     click_y = cavas_y * (self.HEIGHT / 720)
        # else:
        #     click_y = cavas_y * (720 / self.HEIGHT)
        # print ('_mouse_click,mouse position: %s', (cavas_x, cavas_y, self.WIDTH, self.HEIGHT))
        #
        # self.raw_cmd('wait-for-device', 'shell', ' input', 'tap', str(click_x), str(click_y))
        # # self.d.click(int(self.xy.split("x")[0]), int(self.xy.split("x")[1]))
        # time.sleep(2)
        # self.imagetk()

    def _stroke_move(self, event):
        #print "_longmove", event.x, event.y
        self._mouse_motion_xy.append([event.x, event.y])
        self._mouse_motion = "move"
        # self._moved = True
        # self._reset()
        # c = self.canvas
        # x, y = c.canvasx(event.x), c.canvasy(event.y)
        # self._bounds = (self._lastx, self._lasty, x, y)
        # self._center = (self._lastx + x) / 2, (self._lasty + y) / 2
        # self._draw_lines()

    def _mouse_move(self, event):
        print "_mouse_move", event.x, event.y

    def _stroke_done(self, event):
        try:
            x_start = 0
            x_end = 0
            y_start = 0
            y_end = 0
            c = self.canvas
            click_x = 0
            click_y = 0

            cavas_x, cavas_y = (int(c.canvasx(event.x)), int(c.canvasy(event.y)))
            print "_stroke_done","event:", event.x, event.y,"cavas:",cavas_x,cavas_y
            if self._mouse_motion == "click":
                # cavas_x, cavas_y = (int(c.canvasx(event.x)), int(c.canvasy(event.y)))
                stend = datetime.datetime.now()
                ststart = self.cavas_x_y.keys()

                click_x = cavas_x
                click_y = cavas_y
                if int(self.WIDTH) > 360:
                    click_x = click_x * (self.WIDTH / 360.0)
                else:
                    click_x = click_x * (360.0 / self.WIDTH)
                if int(self.HEIGHT) > 720:
                    click_y = click_y * (self.HEIGHT / 720.0)
                else:
                    click_y = click_y * (720.0 / self.HEIGHT)

                print ('_mouse_click,mouse position: %s', (cavas_x, cavas_y, self.WIDTH, self.HEIGHT))
                print "wait:",(stend - ststart[0]).total_seconds()
                if ((stend - ststart[0]).total_seconds() >0.6) and (len(ststart)>0):
                    self.raw_cmd('wait-for-device', 'shell', ' input', 'swipe', str(click_x), str(click_y),str(click_x), str(click_y),'500')
                else:
                    self.raw_cmd('wait-for-device', 'shell', ' input', 'tap', str(click_x), str(click_y))

                self.canvas.itemconfigure('select-bounds', width=2)
                self.textout.insert(END, "点击: " + str(int(click_x)) + " " + str(int(click_y)) + "\n")
                self.textout.update()
                time.sleep(1)
                self.imagetk()
                # print "---",[int(cavas_x), int(cavas_y), int(cavas_x) + 5, int(cavas_y) + 5],cavas_x,cavas_y
                self._draw_bounds([int(cavas_x) - 10, int(cavas_y) - 10, int(cavas_x) + 10, int(cavas_y) + 10])


            elif self._mouse_motion == "move":
                self._mouse_motion = ""
                cavas_x, cavas_y = (int(c.canvasx(event.x)), int(c.canvasy(event.y)))
                click_y = cavas_x
                click_x = cavas_y

                if len(self._mouse_motion_xy) > 3:
                    x_start = self._mouse_motion_xy[0][0]
                    y_start = self._mouse_motion_xy[0][1]
                    x_end = self._mouse_motion_xy[-1][0]
                    y_end = self._mouse_motion_xy[-1][1]
                    if int(self.WIDTH) > 360:
                        x_start = x_start * (self.WIDTH / 360.0)
                        x_end = x_end * (self.WIDTH / 360.0)
                    else:
                        x_start = x_start * (360.0 / self.WIDTH)
                        x_end = x_end * (360.0 / self.WIDTH)
                    if int(self.HEIGHT) > 720:
                        y_start = y_start * (self.HEIGHT / 720.0)
                        y_end = y_end * (self.HEIGHT / 720.0)
                    else:
                        y_start = y_start * (720.0 / self.HEIGHT)
                        y_end = y_end * (720.0 / self.HEIGHT)
                    print ('_mouse_click,mouse position: %s', (cavas_x, cavas_y, self.WIDTH, self.HEIGHT))

                    #print "---",[int(cavas_x), int(cavas_y), int(cavas_x) + 5, int(cavas_y) + 5],cavas_x,cavas_y
                    self._draw_bounds([int(cavas_x)-10, int(cavas_y)-10, int(cavas_x) + 10, int(cavas_y) + 10])
                    if self._mouse_motion_crop == "crop":
                        # self.crop_box = [self._mouse_motion_xy[0][0], self._mouse_motion_xy[0][1], self._mouse_motion_xy[-1][0],
                        #                  self._mouse_motion_xy[-1][1]]
                        c.create_rectangle(self._mouse_motion_xy[0][0], self._mouse_motion_xy[0][1], self._mouse_motion_xy[-1][0],
                                         self._mouse_motion_xy[-1][1], outline='red', tags='select-bounds', width=2)
                        img = Image.open(os.getcwd() + '/maintmp.png')  # 打开图片
                        img.crop([x_start, y_start, x_end,y_end]).save(os.getcwd() + '/maintmp_crop.png')
                        self.textout.insert(END, "保存截图到本地: maintmp_crop.png \n")
                        self.textout.update()
                        self._mouse_motion_crop = ""
                    else:
                        self.raw_cmd('wait-for-device', 'shell', ' input', 'swipe', str(x_start), str(y_start),
                                     str(x_end),
                                     str(y_end))
                        self._mouse_motion_xy = []
                        time.sleep(1)
                        self.imagetk()
            # c = self.canvas
            # x, y = c.canvasx(event.x), c.canvasy(event.y)
            # if self._moved:  # drag action
            #     x, y = (self._lastx + x) / 2, (self._lasty + y) / 2
            #     self._offset = (0, 0)
            # else:
            #     # click action
            #     if self._bounds is None:
            #         cx, cy = (x / self._ratio, y / self._ratio)
            #         if self._uiauto_detect_var.get() and self._hovered_node:
            #             self._selected_node = self._hovered_node
            #             print ("select node: %s", repr(self._selected_node))
            #             print ("center: %s", self._selected_node.bounds.center)
            #             # self._device.click(cx, cy)
            #
            #         self._gencode_text.set('d.click(%d, %d)' % (cx, cy))
            #     else:
            #         (x0, y0, x1, y1) = self.select_bounds
            #         ww, hh = x1 - x0, y1 - y0
            #         cx, cy = (x / self._ratio, y / self._ratio)
            #         mx, my = (x0 + x1) / 2, (y0 + y1) / 2  # middle
            #         self._offset = (offx, offy) = map(int, (cx - mx, cy - my))
            #         poffx = ww and round(offx * 100.0 / ww)  # in case of ww == 0
            #         poffy = hh and round(offy * 100.0 / hh)
            #         self._poffset = (poffx, poffy)
            #         self._gencode_text.set('(%d, %d)' % (cx, cy))  # offset=(%.2f, %.2f)' % (poffx/100, poffy/100))
            #         # self._gencode_text.set('offset=(%.2f, %.2f)' % (poffx/100, poffy/100))

            # ext = ".%dx%d" % tuple(self._size)
            # if self._poffset != (0, 0):
            #     px, py = self._poffset
            #     ext += '.%s%d%s%d' % (
            #         'R' if px > 0 else 'L', abs(px), 'B' if py > 0 else 'T', abs(py))
            # ext += '.png'
            # self._fileext_text.set(ext)
            # self._center = (x, y)  # rember position
            # self._draw_lines()
            # self.canvas.itemconfigure('select-bounds', width=2)
        except Exception, e:
            pass
        finally:
            self.cavas_x_y={}

    def _draw_bounds(self, bounds, color='red', tags='select-bounds'):
        c = self.canvas
        (x0, y0, x1, y1) = bounds
        #c.create_rectangle(x0, y0, x1, y1, outline=color, tags='select-bounds', width=4)
        #print x0,y0,x1,y1
        c.create_oval(x0, y0, x1, y1,  fill = "red")

    def crop_image(self):
        self._mouse_motion_crop = "crop"
        tkinter.messagebox.showinfo(title="提示框", message="用鼠标在右侧屏幕上画出要截取的位置，方框内图像即可保存到本地文件maintmp_crop.png")




        # if self._bounds is None:
        #     return
        # bounds = self.select_bounds
        # # ext = '.%dx%d.png' % tuple(self._size)
        # # tkFileDialog doc: http://tkinter.unpythonic.net/wiki/tkFileDialog
        # save_to = tkFileDialog.asksaveasfilename(**dict(
        #     initialdir=self._save_parent_dir,
        #     defaultextension=".png",
        #     filetypes=[('PNG', ".png")],
        #     title='Select file'))
        # if not save_to:
        #     return
        # save_to = self._fix_path(save_to)
        # # force change extention with info (resolution and offset)
        # save_to = os.path.splitext(save_to)[0] + self._fileext_text.get()
        #
        # self._save_parent_dir = os.path.dirname(save_to)
        #
        # self._image.crop(bounds).save(save_to)
        # self._genfile_name.set(os.path.basename(save_to))
        # self._gencode_text.set('d.click_image(r"%s")' % save_to)


if __name__ == "__main__":
    test = GFXTest()
    test.gettk()

    # test.travelApp("com.android.settings")
    # test.grantPermission("com.myos.camera")
    # test.platformRun2()
    # test.travel2("com.qiku.smartkey")
    # test.recordatx()
