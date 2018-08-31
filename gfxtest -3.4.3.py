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
import importlib
import io
import json
import os
import random
import signal
import socket
import subprocess
import thread
import tkSimpleDialog as dl
import urllib2
import xml.dom.minidom
import xml.etree.ElementTree as ET
from Tkinter import *
from base64 import encodestring
from subprocess import Popen, PIPE

import aircv as ac
import cv2
import numpy as np
import requests
import tkinter.filedialog
import tkinter.messagebox
from PIL import Image, ImageTk, ImageDraw
from PIL import ImageFont
from tkinter import ttk
from uiautomator import Device

import IULTest
import MiniTouch
import MinicapMin
import MyMini
import ReportGen
import videotest
from lib.imcp.mixin import DeviceMixin
from myocr import MYOCRTest

reload(sys)
sys.setdefaultencoding('utf-8')
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

VERSION = "3.4.2"


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
        self.output = str(args[0]) + ".txt"

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
        self.screensave = 3
        self.numberChosen = None
        self.point_cycle = 0
        self.scroll_xy = "v"
        self.scroll_direct = "v"
        self.platfrom_fps = "n"
        self.stop_flag = False
        self.activity = ""
        self.package = ""
        self.apkversion = ""
        self.buildversion = ""
        self.targetSDK = ""
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
        self.serial = ""
        self.serial_b = ""
        # self.serial = self.options.serial_number
        self.fileEdit = "record.text"
        self.startX = 0
        self.startY = 0
        self.radiobutton = []
        self.imglabel = None
        self.radionButton_type_value = None
        self.root = None
        self.canvas = None
        self.status_canvas = None
        self.canvas_performance = None
        self._mouse_motion = ""
        self._mouse_motion_crop = ""
        self._mouse_motion_xy = []
        self.cavas_x_y = {}
        self.crop_box = []
        self.job_plan = True
        self.emmc_start = {}
        self.emmc_end = {}
        self.minicap_ins = None
        self.draw_overflow = 0
        self.stepresult = []
        self.rotation_times = 0
        self.timesLabel = None
        self.entryName = "user"
        self.entryPwd = "user"
        self.minitouch = None
        self.minitch_flag = False
        self.enable_script = False
        self.study_mode_flag = False
        self.installbundleonB = False
        self.canvas_image = None
        self.drawfont = ImageFont.truetype("simsun.ttc", 40)

    def getAllPkg(self):
        try:
            allpkg = []
            out = self.raw_cmd('shell', "pm list package |grep -E '(ape.)|(myos.)|(com.a)'")
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
        try:
            allFile = []
            for filename in (glob.glob(os.getcwd() + u'\*.txt')):  # + glob.glob(os.getcwd() + u'\*.json')):
                allFile.append(filename)
            if len(allFile) == 0:
                return [""]
            else:
                return allFile
        except Exception, e:
            print "get file error"
            import traceback
            traceback.print_exc()
            return [""]

    def inidevice(self):
        self.package = self.getPackage()
        self.activity = self.getActivity()
        self.apkversion, self.buildversion, self.targetSDK = self.getAPKVersion(self.package)
        # size = self.screenSize()
        # self.WIDTH = int(size[0])
        # self.HEIGHT = int(size[1])

    def gettk(self):

        self.root = Tk()
        self.root['bg'] = "White"
        self.root.geometry('1100x720+100+100')
        self.root.title("GFXTest " + VERSION)
        self.canvas = Canvas(self.root, bg="gray", bd=0, highlightthickness=0, relief='ridge')

        # self.status_canvas = Canvas(self.root,bd=0, highlightthickness=0, relief='ridge')
        self.canvas.bind("<Button-1>", self._mouse_click)
        self.canvas.bind_all("<MouseWheel>", self.mouse_wheel_threading)
        self.canvas.bind("<Button-3>", self._mouse_right_click)
        self.canvas.bind("<B1-Motion>", self._stroke_move)
        self.canvas.bind("<B1-ButtonRelease>", self._stroke_done)
        self.canvas.bind_all("<Key>", self.input_text)
        self.canvas.bind_all("<KeyPress-Up>", self.swiptDown)
        self.canvas.bind_all("<KeyPress-Down>", self.swiptUp)
        self.canvas.bind_all("<KeyPress-Left>", self.swiptLeft)
        self.canvas.bind_all("<KeyPress-Right>", self.swiptRight)

        self.canvas.place(x=740, y=0, width=360, height=720)

        imgtitle = Image.open(os.getcwd() + "/lib/res/title.png")  # top
        imgtitle = imgtitle.resize((740, 40), Image.ANTIALIAS)
        phototitle = ImageTk.PhotoImage(imgtitle)
        totallable = Label(self.root)
        totallable.config(image=phototitle, bd=0)
        totallable.place(x=0, y=0, width=740, height=40)

        imgbottom = Image.open(os.getcwd() + "/lib/res/bottom.png")  # bottom
        imgbottom = imgbottom.resize((740, 25), Image.ANTIALIAS)
        photoimgbottom = ImageTk.PhotoImage(imgbottom)
        settingslable = Label(self.root, bg="MediumAquamarine", text='请手动打开设置中的GPU Rendering!', font=("Century"),
                              fg="Crimson")
        settingslable.config(image=photoimgbottom, bd=0)
        settingslable.place(x=0, y=695, width=740, height=25)

        serialRefresh = Label(self.root, bg="White", text='Device List')
        serialRefresh.place(x=2, y=340, width=80, height=30)

        # up down control
        img = Image.open(os.getcwd() + "/lib/res/up.png")  # left
        # img = img.resize((30, 30), Image.ANTIALIAS)
        limg = img.rotate(90)
        photo = ImageTk.PhotoImage(limg)
        l = Button(self.root, command=lambda: self.swiptLeft_nowait(None))
        # l.bind('<Any-Enter>',self.show_hint)
        l.config(image=photo, bd=0)
        l.place(x=240, y=40, width=30, height=30)

        rimg = img.rotate(270)
        photo1 = ImageTk.PhotoImage(rimg)  # right
        r = Button(self.root, command=lambda: self.swiptRight_nowait(None))
        r.config(image=photo1, bd=0)
        r.place(x=270, y=40, width=30, height=30)
        #

        photo2 = ImageTk.PhotoImage(img)  # up
        u = Button(self.root, command=lambda: self.swiptUp_nowait(None))
        u.config(image=photo2, bd=0)
        u.place(x=300, y=40, width=30, height=30)
        #
        dimg = img.rotate(180)
        photo3 = ImageTk.PhotoImage(dimg)  # down
        d = Button(self.root, command=lambda: self.swiptDown_nowait(None))
        d.config(image=photo3, bd=0)
        d.place(x=330, y=40, width=30, height=30)

        roimg = Image.open(os.getcwd() + "/lib/res/r.png")  # rotation
        roimg = roimg.resize((30, 30), Image.ANTIALIAS)
        photo4 = ImageTk.PhotoImage(roimg)
        ro = Button(self.root, command=lambda: self.screen_oration("g"))
        ro.config(image=photo4, bd=0)
        ro.place(x=360, y=40, width=30, height=30)

        baimg = Image.open(os.getcwd() + "/lib/res/b.png")  # back
        photo6 = ImageTk.PhotoImage(baimg)  # 用PIL模块的PhotoImage打开
        ba = Button(self.root, command=lambda: self.press_back(None))
        ba.config(image=photo6, bd=0)
        ba.place(x=390, y=40, width=30, height=30)

        hoimg = Image.open(os.getcwd() + "/lib/res/h.png")  # home
        photo7 = ImageTk.PhotoImage(hoimg)
        ho = Button(self.root, command=self.press_home)
        ho.config(image=photo7, bd=0)
        ho.place(x=420, y=40, width=30, height=30)

        clearimg = Image.open(os.getcwd() + "/lib/res/clear.png")  # home
        photo8 = ImageTk.PhotoImage(clearimg)
        ho = Button(self.root, command=lambda: self.clear_textout(None))
        ho.config(image=photo8, bd=0)
        ho.place(x=450, y=40, width=30, height=30)

        rootimg = Image.open(os.getcwd() + "/lib/res/root.png")  # home
        photo9 = ImageTk.PhotoImage(rootimg)
        root = Button(self.root, command=self.enable_root)
        root.config(image=photo9, bd=0)
        root.place(x=480, y=40, width=30, height=30)

        poimg = Image.open(os.getcwd() + "/lib/res/power.png")  # power
        photo5 = ImageTk.PhotoImage(poimg)
        po = Button(self.root, command=self.press_power)
        po.config(image=photo5, bd=0)
        po.place(x=510, y=40, width=30, height=30)

        lockimg = Image.open(os.getcwd() + "/lib/res/unlock.png")  # power
        photolock = ImageTk.PhotoImage(lockimg)
        polock = Button(self.root, command=self.press_unlock)
        polock.config(image=photolock, bd=0)
        polock.place(x=540, y=40, width=30, height=30)

        cropimg = Image.open(os.getcwd() + "/lib/res/crop.png")  # crop image
        photocropimg = ImageTk.PhotoImage(cropimg)
        crop = Button(self.root, command=self.crop_image_show)
        crop.config(image=photocropimg, bd=0)
        crop.place(x=570, y=40, width=30, height=30)

        saveimg = Image.open(os.getcwd() + "/lib/res/save.png")  # crop image
        saveimgphoto = ImageTk.PhotoImage(saveimg)
        savebutton = Button(self.root, command=lambda: self.control_save(None))
        savebutton.config(image=saveimgphoto, bd=0)
        savebutton.place(x=630, y=40, width=30, height=30)

        openimg = Image.open(os.getcwd() + "/lib/res/open.png")  # crop image
        openimgphoto = ImageTk.PhotoImage(openimg)
        openbutton = Button(self.root, command=self.control_openfile)
        openbutton.config(image=openimgphoto, bd=0)
        openbutton.place(x=600, y=40, width=30, height=30)

        bookkimg = Image.open(os.getcwd() + "/lib/res/book.png")  # power
        photobook = ImageTk.PhotoImage(bookkimg)
        bookbutton = Button(self.root, command=self.study_mode_threading)
        bookbutton.config(image=photobook, bd=0)
        bookbutton.place(x=660, y=40, width=30, height=30)

        blankimg = Image.open(os.getcwd() + "/lib/res/blank.png")  # power
        blankimg = blankimg.resize((80, 30), Image.ANTIALIAS)
        photo51 = ImageTk.PhotoImage(blankimg)
        blanko = Button(self.root, command=self.update_myself)
        blanko.config(image=photo51, bd=0)
        blanko.place(x=690, y=40, width=50, height=30)
        # self.timesLabel = Label(self.root)
        # self.timesLabel.place(x=570, y=40, width=30, height=30)




        serial = self.getAdb2()
        self.radionButton_value = StringVar()
        for i in xrange(len(serial)):
            self.radionButton_value.set(serial[0])
            model = self.getModel(serial[i])
            # if len(serial[i])>15:
            #     model = model[0:4]
            self.radiobutton.append(
                Radiobutton(self.root, bg="White", text=serial[i] + "_" + str(model), variable=self.radionButton_value,
                            value=serial[i],
                            command=lambda: self.on_serial_select(self.root)))
            self.radiobutton[i].place(x=0, y=380 + 30 * i)

        clickxy = Label(self.root, bg="White", text='点击')
        clickxy.place(x=2, y=160, width=30, height=30)
        self.startX = Entry(self.root, bg="white")
        self.startX.place(x=35, y=160, width=90, height=30)
        x = Label(self.root, bg="White", text='x')
        x.place(x=130, y=160, width=10, height=30)
        self.startY = Entry(self.root, bg="white")
        self.startY.place(x=145, y=160, width=90, height=30)
        self.textout = Text(self.root, font=("Courier New", "10"))

        self.textout.bind("<KeyPress-Return>", self.adb_mode)
        self.textout.bind("<Control-KeyPress-s>", self.control_save)
        self.textout.bind("<KeyPress-Escape>", self.clear_textout)

        # self.textout.place(x=240, y=40, width=500, height=555)
        self.textout.place(x=240, y=70, width=500, height=625)

        # imgb = Image.open(os.getcwd() + "/lib/res/up.png")  # bottom
        # imgb = imgb.resize((120, 120), Image.ANTIALIAS)
        # pb = ImageTk.PhotoImage(imgb)
        # self.canvas_image = Label(self.root)
        # self.canvas_image.config(image=None, bg = 'white',bd=0)
        # self.canvas_image.place(x=620, y=575, width=120, height=120)
        # self.canvas_image.place(x=620, y=72, width=120, height=120)

        if len(serial) == 1:
            self.serial = serial[0]
            size = self.screenSize(self.serial)
            self.WIDTH = int(size[0])
            self.HEIGHT = int(size[1])
            self.apkversion, self.buildversion, self.targetSDK = self.getAPKVersion(self.package)
            self.textout.insert(END, "Platform:" + self.buildversion + "\n")
            self.textout.insert(END, "Device:" + self.serial + "\n")
        elif len(serial) > 1:
            self.serial = self.radionButton_value.get()
            size = self.screenSize(self.serial)
            if not size:
                tkinter.messagebox.askokcancel('提示', '请重连设备！')
            self.WIDTH = int(size[0])
            self.HEIGHT = int(size[1])
            self.apkversion, self.buildversion, self.targetSDK = self.getAPKVersion(self.package)
            self.textout.insert(END, "Platform:" + self.buildversion + "\n")
            self.textout.insert(END, "Device:" + self.serial + "\n")
        else:
            print "No any device!"
            tkinter.messagebox.askokcancel('提示', '没有连接设备，请连接设备后重启！')
            # self.textout.insert("1.0", "No any device found!\n")
            sys.exit(1)

        self.typeRecord = IntVar()
        self.typeReplay = IntVar()
        self.typeManu = IntVar()
        self.typeSuper = IntVar()
        self.typeDirect = IntVar()
        manuButton = Checkbutton(self.root, bg="White", variable=self.typeDirect, text='水平', onvalue=1, offvalue=0)
        manuButton.place(x=3, y=195, width=50, height=30)

        self.radionButton_rp_value = StringVar()
        self.radionButton_rp_value.set("v")
        radiobuttonr = Radiobutton(self.root, bg="White", text="记录", variable=self.radionButton_rp_value,
                                   value="r",
                                   command=self.on_recordreplay_record)
        radiobuttonr.place(x=63, y=195, width=50, height=30)

        radiobuttonp = Radiobutton(self.root, bg="White", text="回放", variable=self.radionButton_rp_value,
                                   value="p",
                                   command=self.on_recordreplay_replay)
        radiobuttonp.place(x=125, y=195, width=50, height=30)

        radiobuttonm = Radiobutton(self.root, bg="White", text="手动", variable=self.radionButton_rp_value,
                                   value="m")
        radiobuttonm.place(x=185, y=195, width=50, height=30)
        self.radionButton_type_value = StringVar()
        self.radionButton_type_value.set("fps")
        radiobuttone = Radiobutton(self.root, bg="White", text="FPS", variable=self.radionButton_type_value,
                                   value="fps",
                                   command=self.execute_select)
        radiobuttone.place(x=5, y=45, width=70, height=30)
        radiobuttone = Radiobutton(self.root, bg="White", text="START", variable=self.radionButton_type_value,
                                   value="start",
                                   command=self.execute_select)
        radiobuttone.place(x=75, y=45, width=70, height=30)

        radiobuttone = Radiobutton(self.root, bg="White", text="SCRIPT", variable=self.radionButton_type_value,
                                   value="pressure",
                                   command=self.execute_select)
        radiobuttone.place(x=150, y=45, width=80, height=30)

        packageLabel = Label(self.root, bg="White", text='包名')
        packageLabel.place(x=2, y=80, width=30, height=30)
        number = StringVar()
        self.packageEdit = ttk.Combobox(self.root, width=40, textvariable=number)
        self.packageEdit['values'] = self.getAllPkg()  # 设置下拉列表的值
        self.packageEdit.place(x=35, y=80, width=200, height=30)  # 设置其在界面中出现的位置  column代表列   row 代表行
        # self.packageEdit.current(0)

        fileLabel = Label(self.root, bg="White", text='文件')
        fileLabel.place(x=2, y=120, width=30, height=30)

        number = StringVar()
        self.fileEdit = ttk.Combobox(self.root, width=40, textvariable=number)
        self.fileEdit['values'] = self.getAllFile()  # 设置下拉列表的值
        self.fileEdit.place(x=35, y=120, width=200, height=30)  # 设置其在界面中出现的位置  column代表列   row 代表行
        self.fileEdit.current(0)

        number = StringVar()
        timeLabel = Label(self.root, bg="White", text='次数/时间')
        timeLabel.place(x=2, y=230, width=70, height=30)
        self.numberChosen = ttk.Combobox(self.root, width=12, textvariable=number)
        self.numberChosen['values'] = (1, 3, 5, 10, 20, 30, 100, 500, 1000)
        self.numberChosen.place(x=75, y=232, width=80, height=30)
        self.numberChosen.current(1)
        self.screensave = int(self.numberChosen.get())
        menubar = Menu(self.root)
        help_tool = Menu(menubar, tearoff=0)
        help_tool.add_command(label="帮助", command=self.help)
        help_tool.add_separator()
        help_tool.add_command(label="更新", command=self.update_myself)
        menubar.add_cascade(label='About   |', menu=help_tool)

        tools_menu = Menu(menubar, tearoff=0)
        # tools_menu.add_command(label="网络流量统计", command=self.net_flow_tool)
        # tools_menu.add_separator()
        tools_menu.add_command(label="EMMC/DATA", command=lambda: self.emmc_start_tool(serial))
        # tools_menu.add_command(label="EMMC结束统计", command=lambda: self.emmc_end_tool(serial))
        tools_menu.add_separator()
        # tools_menu.add_command(label="应用兼容性测试", command=self.cavas_step)
        tools_menu.add_command(label="应用兼容性测试", command=self.launche_test)
        tools_menu.add_separator()
        tools_menu.add_command(label="Travel开始", command=self.travel_thread)
        tools_menu.add_separator()
        tools_menu.add_command(label="语言切换开始", command=self.chang_language)
        tools_menu.add_separator()
        tools_menu.add_command(label="Monkey开始", command=self.run_monkey)
        tools_menu.add_command(label="Monkey结束", command=self.killmonkey)
        tools_menu.add_separator()
        tools_menu.add_command(label="GO整机测试", command=self.platformRun2)
        tools_menu.add_separator()
        tools_menu.add_command(label="CTS_V8测试", command=lambda: self.cts_test_threading("cts_8"))
        tools_menu.add_separator()
        tools_menu.add_command(label="SDK版本", command=self.get_sdk_thread)
        menubar.add_cascade(label='专项   |', menu=tools_menu)
        menubar.add_command(label="截图   |", command=self.crop_image_show)
        device_tool = Menu(menubar, tearoff=0)
        device_tool.add_command(label="刷新设备", command=lambda: self.on_serial_refresh(self.root))
        device_tool.add_separator()
        device_tool.add_command(label="断开显示", command=self.on_minicap_killed)
        device_tool.add_separator()
        device_tool.add_command(label="重连显示", command=self.on_minicap_reconnect)
        menubar.add_cascade(label='设备管理   |', menu=device_tool)
        onekey_menu = Menu(menubar, tearoff=0)
        onekey_menu.add_command(label="ROOT", command=self.enable_root)
        onekey_menu.add_command(label="PUSH文件", command=self.push_res)
        onekey_menu.add_command(label="当前应用名", command=self.show_info)
        onekey_menu.add_command(label="安装应用", command=self.install_app)
        onekey_menu.add_command(label="连接PENTURN", command=lambda: self.enable_wifi_thread("PENGUIN", "NA@789_wifi@27"))
        onekey_menu.add_command(label="连接PENTURN_F",
                                command=lambda: self.enable_wifi_thread("PENGUIN_F", "CH_in@ese2f"))
        onekey_menu.add_command(label="执行命令", command=lambda: self.command_shell(serial))
        menubar.add_cascade(label='工具箱   |', menu=onekey_menu)
        menubar.add_command(label="清除屏幕   |", command=lambda: self.clear_textout(None))
        edit_menu = Menu(menubar, tearoff=0)
        edit_menu.add_command(label="打开用例文件", command=self.control_openfile)
        edit_menu.add_separator()
        edit_menu.add_command(label="插入记录脚本", command=lambda: self.control_edit("playrecord"))
        edit_menu.add_separator()
        edit_menu.add_command(label="点击返回", command=lambda: self.control_edit("pressback"))
        edit_menu.add_command(label="点击HOME", command=lambda: self.control_edit("presshome"))
        edit_menu.add_command(label="最近任务", command=lambda: self.control_edit("pressrecent"))
        edit_menu.add_separator()
        edit_menu.add_command(label="启动应用", command=lambda: self.control_edit("startapp"))
        edit_menu.add_command(label="滚动到文字", command=lambda: self.control_edit("scrolltotext"))
        edit_menu.add_command(label="点击文字", command=lambda: self.control_edit("clicktext"))
        edit_menu.add_command(label="等待文字出现", command=lambda: self.control_edit("waitfortext"))
        edit_menu.add_command(label="循环", command=lambda: self.control_edit("loop"))
        edit_menu.add_command(label="点击坐标", command=lambda: self.control_edit("clickscreen"))
        edit_menu.add_command(label="长点击坐标", command=lambda: self.control_edit("longclickscreen"))
        edit_menu.add_command(label="点击图片", command=lambda: self.control_edit("clickimage"))
        edit_menu.add_separator()
        edit_menu.add_command(label="shell命令", command=lambda: self.control_edit("shell"))
        edit_menu.add_command(label="重启设备", command=lambda: self.control_edit("reboot"))
        edit_menu.add_separator()
        edit_menu.add_command(label="检查文字", command=lambda: self.control_edit("checktext"))
        edit_menu.add_command(label="检查图片", command=lambda: self.control_edit("checkimage"))
        edit_menu.add_command(label="对比图片", command=lambda: self.control_edit("imagesimilar"))
        edit_menu.add_separator()
        edit_menu.add_command(label="保存", command=lambda: self.control_save(None))
        menubar.add_cascade(label='脚本测试   |', menu=edit_menu)
        self.root['menu'] = menubar

        execute_Button = Button(self.root, text='START', bg="Orange", font=("Arial", "15"),
                                command=self.exectue_type_thread)
        execute_Button.place(x=0, y=280, width=120, height=40)
        execute_Button = Button(self.root, text='STOP', fg="Orange", bg="Black", font=("Arial", "15"),
                                command=self.execute_stop)
        execute_Button.place(x=120, y=280, width=120, height=40)
        self.installbundle(self.serial)
        self.device_info_thread(self.serial)
        # if os.path.isfile(os.getcwd() + '/maintmp.png'):
        #     img = Image.open(os.getcwd() + '/maintmp.png')  # 打开图片
        #     w, h = img.size
        #     img = img.resize((360, 720), Image.ANTIALIAS)
        #     # image = img.copy()
        #     # image.thumbnail((324, 600), Image.ANTIALIAS)
        #     tkimage = ImageTk.PhotoImage(img)
        #     # self._tkimage = tkimage
        #     self.canvas.config(width=w, height=h)
        #     self.canvas.create_image(0, 0, anchor=tkinter.NW, image=tkimage)
        #     # if len(serial) == 1:
        #     # self.minicap_ins = MinicapMin.screen_with_controls(serial=self.serial, tk=self.root, cav=self.canvas)
        #     # self.minicap_ins.screen_simple()
        self.minicap_ins = MyMini.MyMini(serial=self.serial, tk=self.root, cav=self.canvas)
        self.minicap_ins.screen_simple()
        # self.status_canvas.place(x=240, y=550, width=500, height=150)
        # self.status_canvas.create_rectangle(0, 0, 150, 150,fill='blue')
        # self.root.after(100, self.draw_threading)
        # d56f4c1f2a366a23a883d5d4729ef41a
        # self.auto_close_thread(10)
        # self.permission_user()
        self.minitch_flag = True
        self.minitouch = MiniTouch.Minitouch()
        self.minitouch.teardown()
        self.minitouch_thread()
        self.minitouch.install_and_setup(self.serial, self.WIDTH, self.HEIGHT)
        time.sleep(1)
        # self.mytouch.open_minitouch_stream(self.serial)
        self.update_myself()
        self.root.mainloop()

    def show_info(self):
        act = self.getActivity()
        pkg = self.getPackage()
        self.textout.insert(END, "package:" + pkg + "\n")
        self.textout.insert(END, "activity:" + act + "\n")

        self.textout.update()

    def minitouch_thread(self):
        try:
            cmd = ('adb -s ' + self.serial + ' forward tcp:1111 localabstract:minitouch')
            out = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            time.sleep(1)
            cmds = ("adb -s " + self.serial + " shell /data/local/tmp/minitouch")
            p = subprocess.Popen(cmds, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            time.sleep(1)
        except Exception, e:
            self.minitch_flag = False

    def permission_user(self):

        with open("gfxup.txt", 'ab+') as f:
            tm = 15
            if len(sys.argv) > 1:
                pwd = sys.argv[1]
                ip = self.get_host_ip() + "tn"
                hl = hashlib.md5()
                hl.update(ip)
                sign = hl.hexdigest()
                if sign == pwd:
                    tm = 999
            self.timesback_thread(tm)

    def get_host_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
        finally:
            s.close()
        return ip

    def press_back(self, event):
        self.raw_cmd_nowait('shell', 'input', 'keyevent 4')
        self.textout.insert(END, "Back\n")
        self.textout.update()

    def press_home(self):
        self.raw_cmd_nowait('shell', 'input', 'keyevent 3')
        self.textout.insert(END, "Back To Launcher\n")
        self.textout.update()

    def press_power(self):
        self.raw_cmd_nowait('shell', 'input', 'keyevent 26')
        self.textout.insert(END, "Press Power Key\n")
        self.textout.update()

    def press_unlock(self):

        self.textout.insert(END, "Press UnLock\n")
        self.textout.update()
        self.d.wakeup()
        self.raw_cmd('shell', 'input', 'keyevent 82')
        self.raw_cmd('shell', 'input', 'keyevent 4')

    def execute_stop(self):
        if tkinter.messagebox.askokcancel('提示', '是否终止执行？'):
            self.stop_flag = True
        else:
            self.stop_flag = False

    def exectue_type_thread(self):
        t = threading.Thread(target=self.execute_type).start()

    def execute_type(self):
        zhixingfangshi = self.radionButton_type_value.get()
        if zhixingfangshi == "fps":
            self.gettest()
        elif zhixingfangshi == "start":
            self.testLaunch()
        elif zhixingfangshi == "pressure":
            self.pressure_test()
            self.getLog()

    def pressure_test(self):
        try:
            self.stepresult = []
            report_time = time.strftime("%m%d%H%M%S", time.localtime())
            self.logger = MyLogger(report_time + "_log")
            time.sleep(0.1)
            self.screensave = int(self.numberChosen.get())
            getfile = self.fileEdit.get()
            self.clear_textout(None)
            (path, shotname) = os.path.split(getfile)
            self.textout.insert(1.0, shotname + " script test start.....\n")
            self.textout.update()
            if not os.path.isfile(getfile):
                self.textout.insert(END, "没有输入或找不到文件:" + getfile + "\n")
                self.textout.update()
                return 0
            self.mkdir(os.getcwd() + "/Report")
            self.mkdir(os.getcwd() + "/Report/" + report_time)
            self.mkdir(os.getcwd() + "/pic/" + report_time)
            try:
                # self.stepresult[0] ={'TotalResult': True, 'ResportName': report_time, 'TestFileName': shotname,
                #                         'Times': int(self.screensave)}
                for i in xrange(1, int(self.screensave) + 1):
                    self.logger.debug("[" + str(i) + "] " + shotname.encode('utf-8') + " Start")
                    if self.stop_flag:
                        return 0
                    else:

                        self.playatxthread(getfile, report_time, i)
            except Exception, e:
                import traceback
                traceback.print_exc()
                print "pressure exception"
            finally:
                # print "result:",self.stepresult
                if len(self.stepresult[0][1]) > 0:
                    rt = ReportGen.ReportGen(self.stepresult)
                    passcount, failcount = rt.getresult()
                    self.logger.debug("Result: " + ("Pass" if failcount == 0 else "Fail"))
                    # self.textout.insert(1.0, "_" * 48 + "\n")
                    self.textout.insert(1.0, "Test Finished, Total Result: " + (
                        "Pass" if failcount == 0 else "Fail") + "\n")
                    self.textout.update()
                    rt.report_text()
                    import webbrowser
                    webbrowser.open(os.getcwd() + "/Report/" + report_time + "/Report.html")

        except Exception, e:
            import traceback
            traceback.print_exc()
            pass
        finally:
            self.stop_flag = False

    def execute_select(self):
        zhixingfangshi = self.radionButton_type_value.get()
        if zhixingfangshi == "fps":
            self.textout.delete("1.0", END)
            self.textout.insert(END, "当前设备：" + self.serial + "\n")
            self.textout.insert(END, "选择了：流畅度【FPS测试】\n")
            self.textout.update()
        elif zhixingfangshi == "start":
            self.textout.delete("1.0", END)
            self.textout.insert(END, "当前设备：" + self.serial + "\n")
            self.textout.insert(END, "选择了：启动时间【截图】\n")
            self.textout.update()
        elif zhixingfangshi == "pressure":
            self.textout.delete("1.0", END)
            self.textout.insert(END, "当前设备：" + self.serial + "\n")
            self.textout.insert(END, "选择了：压力测试【脚本控制】\n")
            self.textout.update()

    def help(self):
        try:
            self.textout.delete(1.0, END)
            self.textout.insert(1.0, "Device:" + self.serial + "\n")
        except Exception, e:
            pass
        finally:
            self.textout.insert(END, "Download:\nhttp://ttms.tinno.com/tools/test-tools-version/24\n")
            self.textout.insert(END, "Address:\nlin.shen@tinno.com\n")
            self.textout.update()

    def timesback(self, tm):
        if tm == 999:
            self.timesLabel["text"] = "∞"
        else:
            i = tm
            for k in xrange(0, tm):
                self.timesLabel["text"] = str(i)
                i = i - 1
                time.sleep(60)
            self.minicap_ins.killMinicap()
            self.textout.insert(END, "15分钟连接时间已到，重连请点击设备管理-重连显示!\n")
            self.textout.update()

    def timesback_thread(self, tm):
        flan_run = threading.Thread(target=self.timesback, args=(tm,)).start()

    def on_serial_select(self, tk):
        try:
            self.serial = self.radionButton_value.get()
            size = self.screenSize(self.serial)
            self.WIDTH = int(size[0])
            self.HEIGHT = int(size[1])
            self.apkversion, self.buildversion, self.targetSDK = self.getAPKVersion(self.package)
            self.textout.delete(1.0, END)
            self.textout.insert(END, "Platform:" + self.buildversion + "\n")
            self.textout.insert(END, "Device:" + self.serial + "\n")
            self.textout.insert(1.0, "Reconnect device:" + self.radionButton_value.get() + "\n")
            number = StringVar()
            # self.packageEdit = ttk.Combobox(tk, width=40, textvariable=number)
            self.packageEdit['values'] = self.getAllPkg()  # 设置下拉列表的值
            # self.packageEdit.place(x=35, y=70, width=178, height=30)  # 设置其在界面中出现的位置  column代表列   row 代表行
            # self.packageEdit.current(0)
            self.startX.delete(0, END)
            self.startY.delete(0, END)
            self.installbundle(self.serial)
            self.killMinitouch()
            self.minitch_flag = True
            self.on_minicap_reconnect()
            time.sleep(1)
            self.minitouch.teardown()
            self.minitouch_thread()
            self.minitouch.install_and_setup(self.serial, self.WIDTH, self.HEIGHT)
        except Exception, e:
            self.minitch_flag = False
            import traceback
            traceback.print_exc()

    def on_serial_refresh(self, tk):
        self.textout.bind("<KeyPress-Return>", self.adb_mode)
        self.textout.bind("<KeyPress-Return>", self.adb_mode)
        self.textout.bind("<Control-KeyPress-s>", self.control_save)
        self.textout.bind("<KeyPress-Escape>", self.clear_textout)
        self.radionButton_rp_value.set("v")
        serial = self.getAdb2()
        self.startX.delete(0, END)
        self.startY.delete(0, END)
        if len(serial) == 1:
            self.serial = serial[0]
            size = self.screenSize(self.serial)
            self.WIDTH = int(size[0])
            self.HEIGHT = int(size[1])
        elif len(serial) > 1:
            self.serial = serial[0]
            size = self.screenSize(self.serial)
            self.WIDTH = int(size[0])
            self.HEIGHT = int(size[1])
        else:
            print "No any device!"
            self.textout.insert("1.0", "No any device found!\n")
            self.textout.update()
        self.radiobutton = []
        self.radionButton_value = StringVar()
        for i in xrange(len(serial)):
            model = self.getModel(serial[i])
            # if len(serial[i]) > 15:
            #     model = model[0:4]
            self.radiobutton.append(
                Radiobutton(self.root, bg="White", text=serial[i] + "_" + str(model), variable=self.radionButton_value,
                            value=serial[i],
                            command=lambda: self.on_serial_select(self.root)))
            self.radiobutton[i].place(x=0, y=380 + 30 * i)
        self.radionButton_value.set(serial[0])
        self.on_serial_select(self.root)

    def on_minicap_killed(self):
        if tkinter.messagebox.askokcancel('提示', '是否断开当前设备的屏幕显示？' + self.serial):
            self.minicap_ins.killMinicap()
            self.textout.delete(1.0, END)
            self.textout.insert(1.0, "Stop the device:" + self.radionButton_value.get() + "\n")
            self.textout.update()

    def on_minicap_reconnect(self):
        self.minicap_ins.killMinicap()
        self.apkversion, self.buildversion, self.targetSDK = self.getAPKVersion(self.package)
        self.textout.delete(1.0, END)
        self.textout.insert(END, "Platform:" + self.buildversion + "\n")
        self.textout.insert(END, "Device:" + self.serial + "\n")
        self.textout.insert(1.0, "Reconnect device:" + self.radionButton_value.get() + "\n")
        self.textout.update()
        self.minicap_ins.open_minicap_stream(port=1313, serial=self.serial)
        self.minicap_ins.flag = True
        self.minicap_ins.screen_simple()

    def on_super_replay(self):
        tkinter.messagebox.showinfo(title="提示框",
                                    message="输入测试脚本文件:\n" + "[功能列表：]\n"
                                            + "sleep\n"
                                            + "presshome\n"
                                            + "pressback\n"
                                            + "pressrecent\n"
                                            + "swipe:100,200,100,300\n"
                                            + "drag:100,200,100,300 \n"
                                            + "scrolltotext:TestText\n"
                                            + "screenon:on or off \n"
                                            + "checktext:text\n"
                                            + "waitfortext:text,2\n"
                                            + "checkimage:image.720x1440.png,20\n"
                                            + "imagesimilar:i1,i2 or l1,id or l1,l2\n"
                                            + "clickscreen:200x300\n"
                                            + "clicktext:text\n"
                                            + "longclickscreen:200x300\n"
                                            + "clickimage:image.png\n"
                                            + "startapp:pkg\n"
                                            + "playrecord:record.txt\n"
                                            + "install:app.apk\n"
                                            + "uninstall:com.android.app\n"
                                            + "launch:com.android.app\n"
                                            + "takeshot:1\n"
                                            + "reboot\n"
                                            + "shell\n"
                                            + "ocrface\n"
                                            + "ocrtext:text\n"
                                    )

    def on_recordreplay_record(self):
        self.scroll_direct = "v"
        self.scroll_xy = "r"
        self.raw_cmd('push', os.getcwd() + '/lib/bundle/eventrec', '/data/local/tmp/')
        time.sleep(0.1)
        self.raw_cmd('shell', 'chmod', '777', '/data/local/tmp/eventrec')
        if self.fileEdit.get() == "":
            tkinter.messagebox.showinfo(title="提示框", message="录制回放可以输入文件，默认temp.txt \n 请点击[START]开始！")

    def on_recordreplay_replay(self):
        self.scroll_direct = "v"
        self.scroll_xy = "p"
        self.raw_cmd('push', os.getcwd() + '/lib/bundle/eventrec', '/data/local/tmp/')
        time.sleep(0.1)
        self.raw_cmd('shell', 'chmod', '777', '/data/local/tmp/eventrec')
        if self.fileEdit.get() == "":
            tkinter.messagebox.showinfo(title="提示框", message="录制回放可以输入文件，默认temp.txt \n 请点击[START]开始！")

    def getLog(self):
        try:
            out = self.raw_cmd('shell',
                               'logcat -d |grep -A 1 -E \"FATAL EXCEPTION|ANR in|CRASH:|NOT RESPONDING\"')
            outline = out.split("\r\n")
            find_crash = False
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
                    # self.logger.info("<" + pkg + ">" + " < CRASH:" + str(i) + " >")
                    self.textout.insert(END, "CRASH Found:" + str(i) + "\n")
                    self.textout.update()
                if ("ANR in" in i) or ("NOT RESPONDING:" in i):
                    start = i.find("com")
                    package = i[start:].strip()
                    # readini = self.readinit(os.getcwd() + '/' + str(s) + '.ini', "ANR", package)
                    # print "<" + str(self.serial) + "> " + package + "-> [ANR]: " + i
                    if " " in package:
                        package = package.split()[0]
                        # if "NONE" == readini:
                        #     self.writeinit(os.getcwd() + '/' + str(s) + '.ini', "ANR", package, 1)
                        # elif readini.isdigit():
                        #     readini = int(readini) + 1
                        #     self.writeinit(os.getcwd() + '/' + str(s) + '.ini', "ANR", package, readini)
                        #     # self.writeinit()
                    # self.logger.info("<" + pkg + ">" + " < ANR:" + str(i) + " >")
                    self.textout.insert(END, "ANR Found:" + str(i) + "\n")
        except Exception, e:
            self.textout.insert(END, "Logcat error.\n")
            self.textout.update()
        finally:
            self.textout.insert(END, "Logcat finish.\n")
            self.textout.update()
            # self.raw_cmd('shell', 'logcat', '-c')

    def installbundle(self, serial):
        try:
            self.inidevice()

            out1 = subprocess.check_output(
                "adb -s " + serial + " shell ls /data/local/tmp/bundle.jar; exit 0",
                stderr=subprocess.STDOUT, shell=True)
            if "No such" in out1:
                subprocess.Popen(
                    ['adb', '-s', serial, 'push', os.getcwd() + '/lib/bundle/bundle.jar', '/data/local/tmp/'],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()[0]
            out = subprocess.check_output(
                "adb -s " + serial + " shell ls /data/local/tmp/uiautomator-stub.jar; exit 0",
                stderr=subprocess.STDOUT, shell=True)
            if "No such" in out:
                subprocess.Popen(
                    ['adb', '-s', serial, 'push', os.getcwd() + '/lib/bundle/uiautomator-stub.jar', '/data/local/tmp/'],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()[0]

            out = subprocess.check_output(
                "adb -s " + serial + " shell ls /data/local/tmp/busybox; exit 0",
                stderr=subprocess.STDOUT, shell=True)
            if "No such" in out:
                subprocess.Popen(
                    ['adb', '-s', serial, 'push', os.getcwd() + '/lib/bundle/busybox', '/data/local/tmp/'],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()[0]
                subprocess.Popen(
                    ['adb', '-s', serial, 'shell', 'chmod', '777', '/data/local/tmp/busybox'],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()[0]
            print "install uiautomator and bundle, please wait..."

            outinstall = subprocess.Popen(
                ['adb', '-s', serial, 'install', 'pm', 'list', 'package', 'com.github.uiautomator'],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()[0]
            if "com.github.uiautomator" not in outinstall:
                subprocess.Popen(
                    ['adb', '-s', serial, 'install', '-r', os.getcwd() + '/lib/bundle/app.apk'],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()[0]
                subprocess.Popen(
                    ['adb', '-s', serial, 'install', '-r', os.getcwd() + '/lib/bundle/app-test.apk'],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()[0]
            # self.raw_cmd('am', 'start','-W','com.github.uiautomator/com.github.uiautomator.MainActivity')

            out = subprocess.check_output(
                "adb -s " + serial + " shell ls /data/local/tmp/minicap; exit 0",
                stderr=subprocess.STDOUT, shell=True)
            if "No such" in out:
                cpu = subprocess.Popen(
                    ['adb', '-s', serial, 'shell', 'getprop', 'ro.product.cpu.abi'],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()[0]
                cpu = cpu.strip()
                sdk = subprocess.Popen(
                    ['adb', '-s', serial, 'shell', 'getprop', 'ro.build.version.sdk'],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()[0]
                sdk = sdk.strip()
                subprocess.Popen(
                    ['adb', '-s', serial, 'push', os.getcwd() + '/lib/' + sdk + '/' + cpu + '/minicap.so',
                     '/data/local/tmp/'],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
                subprocess.Popen(
                    ['adb', '-s', serial, 'push', os.getcwd() + '/lib/' + sdk + '/' + cpu + '/minicap',
                     '/data/local/tmp/'],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
                subprocess.Popen(
                    ['adb', '-s', serial, 'shell', 'chmod',
                     '777', '/data/local/tmp/minicap'],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
                subprocess.Popen(
                    ['adb', '-s', serial, 'push', os.getcwd() + '/lib/' + cpu + '/minitouch',
                     '/data/local/tmp/'],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
                subprocess.Popen(
                    ['adb', '-s', serial, 'shell', 'chmod',
                     '777', '/data/local/tmp/minitouch'],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
            return True
        except Exception, e:
            return False
        finally:
            print "Push resource finish,please wait for minicap start...."

    def screenSize(self, serial):
        try:
            out = subprocess.Popen(['adb', '-s', serial, 'shell', 'wm', 'size'],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()[0]
            out = out.split()[-1].split("x")
            return out
        except Exception, e:
            print "No any device!"
            tkinter.messagebox.askokcancel('提示', '请adb devices查看连接的设备，设备异常！')
            # self.textout.insert("1.0", "No any device found!\n")
            sys.exit(1)

    def getPackage(self):
        try:
            out = self.shell_cmd('getprop ro.build.version.sdk')
            sdk = int(out.strip())
            if sdk < 26:
                getp = self.shell_cmd('dumpsys activity |grep mFocusedActivity')
            else:
                getp = self.shell_cmd('dumpsys activity |grep mResumedActivity')
            # out = self.raw_cmd( 'shell', 'ps', '|grep', 'minicap')
            start = getp.find("com")
            end = getp.find('/')
            package = getp[start:end].strip()
            # apkversion = self.raw_cmd( 'shell', 'dumpsys', "package", package, "|", "grep",'versionName', '|head -n 1')
            return package
        except Exception, e:
            return ""

    def getModel(self, serial):
        cmds = ['adb'] + ['-s'] + [serial] + ['shell', 'getprop', 'ro.product.model']
        # cmds = ['adb'] + ['-s'] + [serial] + ['shell', 'getprop', 'ro.vendor.product.model']
        p = subprocess.Popen(cmds, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        c = p.communicate()[0].strip().replace(" ", "_")
        # c = p.communicate()[0]
        return c

    def getAPKVersion(self, pkg):
        apkversion = ""
        targetSDKapkversion = ""
        buildversion = \
            self.raw_cmd('shell', 'getprop', 'ro.custom.build.version').strip()
        if self.package != "":
            apkversion = \
                self.raw_cmd('shell', 'dumpsys', "package", pkg, "|", "grep", 'versionName')
            # targetSDKapkversion = \
            #     self.raw_cmd('shell', 'dumpsys', "package", self.package, "|", "grep", 'targetSdk', '| cut -d \'=\' -f 4')
            targetSDKapkversion = \
                self.raw_cmd('shell', 'dumpsys', "package", pkg, "|", "grep", 'targetSdk')
            try:
                targetSDKapkversion = targetSDKapkversion[targetSDKapkversion.find("targetSdk"):].split("=")[1]
            except Exception, e:
                pass
            if "versionName=" in apkversion:
                apkversion = apkversion.replace("versionName=", "").strip().split()[0]
            if "_" in apkversion:
                apkversion = apkversion.split("_")[0]
        return apkversion, buildversion, targetSDKapkversion

    def getActivity(self):
        try:
            out = self.raw_cmd('shell', 'getprop', 'ro.build.version.sdk')
            sdk = int(out.strip())
            if sdk < 26:
                getp = self.raw_cmd('shell', 'dumpsys', 'activity', '|grep', 'mFocusedActivity')
            else:
                getp = self.raw_cmd('shell', 'dumpsys', 'activity', '|grep', 'mResumedActivity')
            # out = self.raw_cmd( 'shell', 'ps', '|grep', 'minicap')
            start = getp.find("com")
            end = getp.find('/')
            package = getp[start:end].strip()  # "com.android.settings"
            endactivty = getp[start:].strip()  # "com.android.setings/.abcdef xyszn"
            endactivty1 = endactivty.find(" ")  #
            aend = endactivty[:endactivty1].strip("\r\n")  # "com.android.setings/.abcdef"

            if "/." in aend:
                # activity = aend.replace("/.", "/" + package + ".")
                activity = package + aend.split("/")[1]
            elif "/" in aend:
                activity = aend.split("/")[1]
            return activity
        except Exception, e:
            return ""

    # def setup_arg_parser(self):
    #     usage = "usage: %prog -c TEST_CAMPAIGN [OPTIONS]"
    #     parser = OptionParser(usage=usage)
    #     mandatory_group = OptionGroup(parser, "MANDATORIES")
    #
    #     mandatory_group.add_option("-c",
    #                                metavar=u"fps或者start启动时间",
    #                                default="fps",
    #                                dest="campaign_name")
    #     parser.add_option_group(mandatory_group)
    #     optional_group = OptionGroup(parser, "OPTIONS")
    #     optional_group.add_option("-s",
    #                               metavar=u"123456 |设备号,只有1个设备时无需设置|",
    #                               default="",
    #                               dest="serial_number")
    #
    #     optional_group.add_option("-p",
    #                               metavar=u"com.android.settings |测试包名,默认当前窗口|",
    #                               default="",
    #                               dest="test_package")
    #
    #     optional_group.add_option("-t",
    #                               metavar=u"5 |截图时间默认3秒|",
    #                               default="3",
    #                               dest="screen_save")
    #
    #     optional_group.add_option("-x",
    #                               metavar=u"200x300 |点击点xy坐标|",
    #                               default="",
    #                               dest="screen_xy")
    #
    #     optional_group.add_option("-a",
    #                               metavar=u"com.android.settings/com.android.settings.Settings  |包名全称|",
    #                               default="",
    #                               dest="pkg_activity")
    #
    #     optional_group.add_option("-d",
    #                               metavar=u"v |滑动方向,h 水平 v 垂直 m 手动 默认v r 录制 p 回放|",
    #                               default="v",
    #                               dest="scrool_xy")
    #
    #     optional_group.add_option("-u",
    #                               metavar=u"图形界面",
    #                               default="n",
    #                               dest="gfxtest_gui")
    #
    #     optional_group.add_option("-r",
    #                               metavar=u"y |流畅度整机测试,默认n|",
    #                               default="n",
    #                               dest="platfrom_fps")
    #
    #     optional_group.add_option("-g",
    #                               metavar=u"g |不测FPS，用于提高其他测试的性能|",
    #                               default="y",
    #                               dest="enable_fps")
    #
    #     parser.add_option_group(optional_group)
    #     return parser

    def raw_cmd(self, *args):
        try:
            cmds = ['adb'] + ['-s'] + [self.serial] + list(args)
            p = subprocess.Popen(cmds, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            c = p.communicate()[0]
            return c
        except Exception, e:
            pass

    def raw_cmd_nowait(self, *args):
        try:

            cmds = ['adb'] + ['-s'] + [self.serial] + list(args)
            subprocess.Popen(cmds, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except Exception, e:
            pass

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

    def run_monkey(self):
        serial = [self.serial]
        if tkinter.messagebox.askokcancel('提示', '运行所有设备点<是>,<否>仅仅执行选择的设备'):
            serial = self.getAdb2()
        else:
            pass
        for i in xrange(0, len(serial)):
            self.serial = serial[i]
            self.textout.insert(END, self.serial + " run monkey at: " + str(
                datetime.datetime.now().strftime("%m/%d-%H:%M:%S")) + " \n")
            self.textout.update()
            # self.raw_cmd('push', os.getcwd() + '/lib/bundle/lan.sh',
            #              '/data/local/tmp/')
            # self.raw_cmd('shell', 'chmod', '777', '/data/local/tmp/lan.sh')
            # self.raw_cmd('push', os.getcwd() + '/lib/bundle/language_config.ini',
            #              '/sdcard/')
            # self.raw_cmd('push', os.getcwd() + '/lib/bundle/travel_config.ini',
            #              '/sdcard')
            # self.raw_cmd('mkdir', '-p', '/sdcard/test')
            # outinstallest = self.raw_cmd('shell', 'pm', 'list', 'package',
            #                              'com.tinno.test.appstraveler')
            # if "com.tinno.test.appstraveler" not in outinstallest:
            #     self.raw_cmd('install', '-t', '-r', os.getcwd() + '/lib/bundle/lan.apk')
            # outinstallest = self.raw_cmd('shell', 'pm', 'list', 'package',
            #                              'com.tinno.test.appstraveler.test')
            # if "com.tinno.test.appstraveler.test" not in outinstallest:
            #     self.raw_cmd('install', '-t', '-r', os.getcwd() + '/lib/bundle/lan-test.apk')
            # self.raw_cmd('shell', 'pm', 'grant', 'com.tinno.test.appstraveler',
            #              'android.permission.CHANGE_CONFIGURATION')
            # self.grantPermission("com.tinno.test.appstraveler")
            # self.grantPermission("com.tinno.test.appstraveler.test")
            # subprocess.call("adb -s " + self.serial + " shell am instrument -w -r -e debug false -e listener de.schroepf.androidxmlrunlistener.XmlRunListener -e class com.tinno.autotravel.AppsTraveler#testLan com.tinno.test.appstraveler.test/android.support.test.runner.AndroidJUnitRunner")
            # self.screensave = int(self.numberChosen.get())
            # self.raw_cmd('shell', 'sh',  '/data/local/tmp/lan.sh &')
            # lan_run = threading.Thread(target=self.chang_language).start()
            monkey_run = threading.Thread(target=self.monkeythread).start()
            time.sleep(2)
            print "monkey:", self.serial
            # ct = 0
            # timeNow = time.time()
            # while ct <= int(self.screensave):
            #     time.sleep(20)
            #     ct = time.time() - timeNow
            #
            # self.killmonkey()
            # self.getLog()

    def mkdir(self, path):
        path = path.strip()
        path = path.rstrip("\\")
        isExists = os.path.exists(path)
        if not isExists:
            os.makedirs(path)
            return True
        else:
            return False

    def chang_language(self):
        if tkinter.messagebox.askokcancel('提示', '目录中lib/bundle/language_config.ini为语言配置文件！'):
            self.killlc()
            self.textout.insert(END, "Run LC threading：" + str(
                datetime.datetime.now().strftime("%m/%d-%H:%M:%S")) + " \n")
            self.textout.update()
            self.raw_cmd('push', os.getcwd() + '/lib/bundle/lan.sh',
                         '/data/local/tmp/')
            self.raw_cmd('shell', 'chmod', '777', '/data/local/tmp/lan.sh')
            self.raw_cmd('push', os.getcwd() + '/lib/bundle/language_config.ini',
                         '/sdcard/')
            self.raw_cmd('push', os.getcwd() + '/lib/bundle/travel_config.ini',
                         '/sdcard')
            self.raw_cmd('mkdir', '-p', '/sdcard/test')
            outinstallest = self.raw_cmd('shell', 'pm', 'list', 'package',
                                         'com.tinno.test.appstraveler')
            if "com.tinno.test.appstraveler" not in outinstallest:
                self.raw_cmd('install', '-t', '-r', os.getcwd() + '/lib/bundle/lan.apk')
            outinstallest = self.raw_cmd('shell', 'pm', 'list', 'package',
                                         'com.tinno.test.appstraveler.test')
            if "com.tinno.test.appstraveler.test" not in outinstallest:
                self.raw_cmd('install', '-t', '-r', os.getcwd() + '/lib/bundle/lan-test.apk')
            self.raw_cmd('shell', 'pm', 'grant', 'com.tinno.test.appstraveler',
                         'android.permission.CHANGE_CONFIGURATION')
            self.grantPermission("com.tinno.test.appstraveler")
            self.grantPermission("com.tinno.test.appstraveler.test")
            # subprocess.call("adb -s " + self.serial + " shell am instrument -w -r -e debug false -e listener de.schroepf.androidxmlrunlistener.XmlRunListener -e class com.tinno.autotravel.AppsTraveler#testLan com.tinno.test.appstraveler.test/android.support.test.runner.AndroidJUnitRunner")
            # self.screensave = int(self.numberChosen.get())
            # self.raw_cmd('shell', 'sh',  '/data/local/tmp/lan.sh &')
            # lan_run = threading.Thread(target=self.chang_language).start()
            t = threading.Thread(target=self.lcthread).start()

    def monkeythread(self):
        try:
            package_Edit = self.packageEdit.get()
            print self.serial
            if package_Edit == "":
                self.raw_cmd('shell', 'monkey',
                             '--throttle', '1000', '-s', '10',
                             '--ignore-security-exceptions',
                             '--ignore-crashes', '--ignore-timeouts', '--ignore-native-crashes', '-v', '200000000',
                             '>/mnt/sdcard/monkeylog.log 2>&1')
            else:
                self.package = package_Edit
                self.raw_cmd('shell', 'monkey', '-p', str(self.package),
                             '--throttle', '1000', '-s', '10',
                             '--ignore-security-exceptions',
                             '--ignore-crashes', '--ignore-timeouts', '--ignore-native-crashes', '-v', '200000000',
                             '>/mnt/sdcard/monkeylog.log 2>&1')
        except Exception, e:
            return False

    def lcthread(self):
        try:
            self.raw_cmd('shell', 'am', 'instrument', '-w', '-r', '-e', 'debug false', '-e', 'class',
                         'com.tinno.autotravel.AppsTraveler#testLan com.tinno.test.appstraveler.test/android.support.test.runner.AndroidJUnitRunner 2>&1')
        except Exception, e:
            return False

    def removeFileInFirstDir(self, targetDir):
        for file in os.listdir(targetDir):
            targetFile = os.path.join(targetDir, file)
            if os.path.isfile(targetFile):
                os.remove(targetFile)

    def screen_oration(self, ori):
        try:
            self.textout.insert(END, "旋转屏幕！\n")
            self.textout.update()
            if (ori == "g"):
                self.d.freeze_rotation(0)
                if self.rotation_times == 0:
                    self.rotation_times = self.rotation_times + 1
                    self.d.orientation = "l"
                elif self.rotation_times == 1:
                    self.rotation_times = self.rotation_times + 1
                    self.d.orientation = "r"
                elif self.rotation_times == 2:
                    self.rotation_times = 0
                    self.d.orientation = "n"
            else:
                self.d.orientation = ori
        except Exception, e:
            return False

    def input_text(self, event):
        # res = dl.askstring('输入文字', '请输入文字：', initialvalue='')
        ky = event.keysym
        if ky == "BackSpace":
            cmds = 'adb -s ' + self.serial + ' shell input keyevent KEYCODE_DEL'
        else:
            cmds = 'adb -s ' + self.serial + ' shell input' + ' text ' + '\\\"' + event.char + '\\\"'
        p = subprocess.Popen(cmds, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # print "input text:",event.char,event.keysym

    def delete_text(self, event):
        # print "delete "
        cmds = 'adb -s ' + self.serial + ' shell input keyevent KEYCODE_DEL'
        p = subprocess.Popen(cmds, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        c = p.communicate()[0]

    def swiptDown(self, event):
        self.shell_cmd(
            'input swipe ' + str(self.WIDTH / 2) + " " + str(self.HEIGHT * 0.7) + " " + str(self.WIDTH / 2) + " " + str(
                self.HEIGHT * 0.2))

    def swiptDown_nowait(self, event):
        self.raw_cmd_nowait('shell', 'input', 'swipe', str(self.WIDTH / 2), str(self.HEIGHT * 0.7), str(self.WIDTH / 2),
                            str(self.HEIGHT * 0.2))

    def swiptUp(self, event):
        self.shell_cmd(
            'input swipe ' + str(self.WIDTH / 2) + " " + str(self.HEIGHT * 0.3) + " " + str(self.WIDTH / 2) + " " + str(
                self.HEIGHT * 0.7))

    def swiptUp_nowait(self, event):
        self.raw_cmd_nowait('shell', 'input', 'swipe', str(self.WIDTH / 2), str(self.HEIGHT * 0.3), str(self.WIDTH / 2),
                            str(self.HEIGHT * 0.7))

    def swiptRight(self, event):
        self.shell_cmd(
            'input swipe ' + str(self.WIDTH - 50) + " " + str(self.HEIGHT / 2) + " 50 " + str(self.HEIGHT / 2))

    def swiptRight_nowait(self, event):
        self.raw_cmd_nowait('shell', 'input', 'swipe', str(self.WIDTH - 50), str(self.HEIGHT / 2), "50 ",
                            str(self.HEIGHT / 2))

    def swiptLeft(self, event):
        self.shell_cmd(
            'input swipe  50 ' + str(self.HEIGHT / 2) + " " + str(self.WIDTH - 50) + " " + str(self.HEIGHT / 2))

    def swiptLeft_nowait(self, event):
        self.raw_cmd_nowait('shell', 'input', 'swipe', '50', str(self.HEIGHT / 2), str(self.WIDTH - 50),
                            str(self.HEIGHT / 2))

    def screenShot(self, path):
        try:
            # out = subprocess.Popen(
            #     ['adb', '-s', self.serial, 'shell', 'LD_LIBRARY_PATH=/data/local/tmp', '/data/local/tmp/minicap',
            #      '-i', ],
            #     stdout=subprocess.PIPE).communicate()[0]
            # m = re.search('"width": (\d+).*"height": (\d+).*"rotation": (\d+)', out, re.S)
            # w, h, r = map(int, m.groups())
            # w, h = min(w, h), max(w, h)
            params = '{x}x{y}@{x1}x{y1}/{r}'.format(x=self.WIDTH, y=self.HEIGHT, x1=self.WIDTH, y1=self.HEIGHT, r=0)

            # params = '{x}x{y}@{x1}x{y1}/{r}'.format(x=w, y=h, x1=w, y1=h, r=0)
            # cmd = 'shell LD_LIBRARY_PATH=/data/local/tmp /data/local/tmp/minicap -P %s' % params + ' -S -s > /sdcard/maintmp.png'
            # pullcmd = 'pull /sdcard/maintmp.png ./maintmp.png'

            self.raw_cmd('shell', 'LD_LIBRARY_PATH=/data/local/tmp', '/data/local/tmp/minicap', '-P %s' % params,
                         '-S -s > /sdcard/maintmp.png')
            self.raw_cmd('pull', '/sdcard/maintmp.png', str(path))

        except Exception, e:
            pass

    def swipe2(self, dir):
        try:
            if "systemui" in self.package:
                self.raw_cmd('shell', 'input', 'swipe', str(self.WIDTH / 2), "1",
                             str(self.WIDTH / 2), str(self.HEIGHT * 0.7))
                self.raw_cmd('shell', 'input', 'swipe', str(self.WIDTH - 50), str(self.HEIGHT / 2),
                             "50",
                             str(self.HEIGHT / 2))
                self.raw_cmd('shell', 'input', 'keyevent 26')
                time.sleep(0.1)
                self.raw_cmd('shell', 'input', 'keyevent 26')
                time.sleep(0.1)
                self.raw_cmd('shell', 'input', 'keyevent 4')
            elif self.scroll_xy == "m":
                pass
            else:
                if dir == "vh" or dir == "hv":
                    self.swiptDown(None)
                    self.swiptUp(None)
                    self.swiptRight(None)
                    self.swiptLeft(None)
                elif dir == "v":
                    self.swiptDown(None)
                    self.swiptUp(None)
                    self.swiptDown(None)
                    self.swiptUp(None)
                elif dir == "h":
                    self.swiptRight(None)
                    self.swiptLeft(None)
                    self.swiptRight(None)
                    self.swiptLeft(None)

        finally:
            pass
            # self.screenShot(os.getcwd() + "/pic/" + self.package + str(datetime.datetime.now().second) + ".png")

    def gfxclean(self):
        results = self.raw_cmd('shell', 'dumpsys', 'gfxinfo', self.package, 'reset')

    def swipesystemui(self):
        self.raw_cmd('shell', 'input', 'swipe', str(self.WIDTH / 2), "1",
                     str(self.WIDTH / 2), str(self.HEIGHT * 0.7))
        self.raw_cmd('shell', 'input', 'swipe', str(self.WIDTH - 50), str(self.HEIGHT / 2),
                     "50",
                     str(self.HEIGHT / 2))
        self.raw_cmd('shell', 'input', 'swipe', str(self.WIDTH - 50), str(self.HEIGHT / 2),
                     "50",
                     str(self.HEIGHT / 2))
        self.raw_cmd('shell', 'input', 'keyevent', '4')

    def gfxtest(self, pkg):
        if "systemui" in self.package:
            return self.gfxtest2(pkg)
        else:
            return self.gtest(pkg)

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

            results = self.raw_cmd('shell', 'dumpsys', 'gfxinfo', pkg)
            if len(self.fileEdit.get()) > 1:
                results = self.raw_cmd('shell', 'dumpsys', 'gfxinfo', pkg, "|grep -A 120", self.fileEdit.get())
            pt = False
            frames = []
            for i in results.split("\r"):
                if "Draw" in i and "Process" in i and "Execute" in i:
                    pt = True
                    j = 0
                    continue
                if pt and len(i) > 1:
                    resw = re.findall(my_re, i)
                    # if (j <= 120) & (i != "") & (len(i) > 1):
                    if len(resw) == 0:
                        frames.append(i.split())
                    else:
                        pt = False
            for frame in frames:
                if len(frame) == 4:
                    try:
                        if float(frame[0]) > 16.67:  # >16.67s
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

    def gfxtest2(self, pkg):
        try:
            fps = 0
            jank_count = 0
            results = self.raw_cmd('shell', 'dumpsys', 'gfxinfo', pkg)
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
        persion = self.raw_cmd('shell', 'getprop', 'ro.internal.build.version')
        if "8.0" in persion:
            thread.start_new_thread(
                self.raw_cmd('shell', 'sh /data/local/tmp/fps.sh -t 60 -w ' + activity + "#0",
                             stdout=subprocess.PIPE), ("Thread-1", 2,))
        else:
            thread.start_new_thread(
                self.raw_cmd('shell', 'sh /data/local/tmp/fps.sh -t 60 -w ' + activity,
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
            # self.raw_cmd( 'shell', 'setprop', 'debug.hwui.profile', 'visual_bars',
            #              stdout=subprocess.PIPE)  # visual_bars
            # self.raw_cmd( 'shell',
            #              'monkey', '-p com.android.settings -c', 'android.intent.category.LAUNCHER', '1',
            #              stdout=subprocess.PIPE )
            # time.sleep(0.2)
            # self.raw_cmd( 'shell', 'input', 'keyevent', '4',
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

            package_Edit = self.packageEdit.get()
            if package_Edit == "":
                self.package = self.getPackage()
            else:
                self.package = package_Edit
            self.gfxclean()
            # self.apkversion = self.getAPKVersion()

            self.textout.delete(1.0, END)
            if (self.scroll_xy == "v") and (self.scroll_direct == "h"):
                self.textout.insert(END, "FPS Horizon Mode" + ".\n")
            elif (self.scroll_xy == "v") and (self.scroll_direct == "v"):
                self.textout.insert(END, "FPS Vertical Mode" + ".\n")
            elif self.scroll_xy == "m":
                self.textout.insert(END, "FPS By Manual" + ".\n")
            elif self.scroll_xy == "s":
                self.textout.insert(END, "Script Control Mode" + ".\n")
            elif self.scroll_xy == "r":
                self.textout.insert(END, "Record Mode" + ".\n")
            elif self.scroll_xy == "p":
                self.textout.insert(END, "FPS Replay" + ".\n")
            self.textout.insert(END, "Platform:" + self.buildversion + "\n")
            self.textout.insert(END, "Package:" + self.package + " ver=" + self.apkversion + " sdk=" + str(
                self.targetSDK) + "\n")
            self.textout.insert(END, "-" * 48 + "\n")
            self.textout.update()

            if self.scroll_xy == "m" or self.scroll_xy == "p":
                if self.scroll_xy == "p":
                    ref = self.fileEdit.get()
                    if ref == "":
                        ref = "temp.txt"
                    for i in xrange(1, int(self.screensave) + 1):
                        if self.stop_flag:
                            return 0
                        else:
                            pkg_main = self.package
                            pkg_filter = self.raw_cmd('shell', 'dumpsys', 'gfxinfo', '|grep', self.package).split("\n")[
                                0]
                            if self.package in pkg_filter and "[" in pkg_filter:
                                pkg_main = pkg_filter[pkg_filter.find("[") + 1:pkg_filter.find("]")]
                            self.raw_cmd('shell', 'dumpsys', 'gfxinfo', self.package, 'reset')
                            self.textout.insert(END, "播放次数:" + str(i) + ", 文件:" + str(ref) + "\n")
                            self.textout.update()
                            self.replay(ref)

                            result = self.gfxtest(pkg_main)
                            if (result[0] > 10) & (result[2] > 0):
                                total_count += 1
                                frame_count += result[0]
                                jank_count += result[1]
                                fps = int(fps + result[2])
                                draw_over = (draw_over + result[3])
                                self.textout.insert(END,
                                                    "<" + str(i) + "> FPS=" + str(result[2]) + ", Draw=" + str(
                                                        result[3]) + "%,Total=" + str(
                                                        result[0]) + ",Janks=" + str(result[1]) + "\n")
                            else:
                                self.textout.insert(END, "滑动太少，没有足够的数据！\n")
                        self.textout.update()
                        # self.getLog(self.package)
                        self.screenShot(os.getcwd() + "/pic/" + self.package + str(
                            datetime.datetime.now().strftime("%m_%d_%H_%M_%S")) + ".png")
                elif self.scroll_xy == "m":
                    self.textout.insert(END, "3秒后开始滑动！\n")
                    self.textout.update()
                    time.sleep(1)
                    self.textout.insert(END, "2秒后开始滑动！\n")
                    self.textout.update()
                    # self.raw_cmd('shell', 'dumpsys', 'gfxinfo', self.package, 'reset')
                    time.sleep(1)
                    self.textout.insert(END, "开始滑动！\n")
                    self.textout.update()
                    total_count = 1
                    time.sleep(int(self.screensave))
                    if package_Edit == "":
                        self.package = self.getPackage()
                    else:
                        self.package = package_Edit
                    result = self.gfxtest(self.package)
                    print result
                    if (result[0] > 10) & (result[2] >= 0):
                        frame_count += result[0]
                        jank_count += result[1]
                        fps = int(fps + result[2])
                        draw_over = (draw_over + result[3])
                        self.textout.insert(END, "<" + str(total_count) + "> FPS=" + str(result[2]) + " Draw=" + str(
                            result[3]) + "%,Total=" + str(
                            result[0]) + ",Janks=" + str(result[1]) + "\n")
                    else:
                        self.textout.insert(END, "滑动太少，没有足够的数据！\n")
                    self.textout.update()
                    self.screenShot(os.getcwd() + "/pic/" + self.package + str(
                        datetime.datetime.now().strftime("%m_%d_%H_%M_%S")) + ".png")
            else:
                for m in xrange(0, int(self.screensave)):
                    if self.stop_flag:
                        return 0
                    else:
                        if x != "" and y != "":
                            self.raw_cmd('shell', ' input', 'tap', str(x), str(y))
                            time.sleep(2)
                        pkg_main = self.package
                        pkg_filter = self.raw_cmd('shell', 'dumpsys', 'gfxinfo', '|grep', self.package).split("\n")[0]
                        if self.package in pkg_filter and "[" in pkg_filter:
                            pkg_main = pkg_filter[pkg_filter.find("[") + 1:pkg_filter.find("]")]
                        self.raw_cmd('shell', 'dumpsys', 'gfxinfo', self.package, 'reset')
                        self.swipe2(self.scroll_direct)
                        result = self.gfxtest(pkg_main)
                        # if (result[0] < 30):
                        #     self.swipe2(self.scroll_direct)
                        #     self.swipe2(self.scroll_direct)
                        #     result = self.gfxtest()
                        if (result[0] > 10) and (result[2] >= 0):
                            total_count += 1
                            frame_count += result[0]
                            jank_count += result[1]
                            fps += result[2]
                            draw_over += result[3]

                            self.textout.insert(END,
                                                "<" + str(total_count) + "> FPS=" + str(result[2]) + " Draw=" + str(
                                                    result[3]) + "%,Total=" + str(
                                                    result[0]) + ",Janks=" + str(result[1]) + "\n")

                        else:
                            self.textout.insert(END, "滑动太少，没有足够的数据，或者GPU测试模式未开！\n")
                        # self.imagetk()
                        self.textout.update()
                        self.screenShot(os.getcwd() + "/pic/" + self.package + str(
                            datetime.datetime.now().strftime("%m_%d_%H_%M_%S")) + ".png")

            if (total_count > 0) & (frame_count > 20):
                fps = fps / total_count
                draw_over = int((draw_over / total_count) / 0.75)

                self.textout.insert(END, "-" * 48 + "\n")
                self.textout.insert(END, str(total_count) + u"次平均FPS: " + str(fps) + u";应用丢帧: " + str(
                    draw_over) + "%," + u"\n总帧数:" + str(
                    frame_count) + u",丢帧数:" + str(jank_count) + u",丢帧率:" + str(
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
            self.stop_flag = False
            self.textout.insert(END, "-" * 48 + "\n")
            self.textout.insert(END, "测试完成\n")
            self.textout.update()
            return fps, draw_over

    def killmonkey(self):
        try:
            serial = [self.serial]
            if tkinter.messagebox.askokcancel('提示', '停止所有设备点<是>,<否>仅仅停止选择的设备'):
                serial = self.getAdb2()
            else:
                pass
            for i in xrange(0, len(serial)):
                self.serial = serial[i]
                out = self.raw_cmd('shell', '/data/local/tmp/busybox ps | grep commands.monkey | grep -v "grep"')
                for i in out.split("\n"):
                    if " " in i:
                        ps = Popen("adb  -s " + self.serial + " shell kill " + i.split()[0], shell=True, stdout=PIPE,
                                   stderr=PIPE)
                        ps.communicate()

                out = self.raw_cmd('shell', '/data/local/tmp/busybox ps | grep AndroidJUnitRunner | grep -v "grep"')
                for i in out.split("\n"):
                    if " " in i:
                        ps = Popen("adb  -s " + self.serial + " shell kill " + i.split()[0], shell=True, stdout=PIPE,
                                   stderr=PIPE)
                        ps.communicate()
                self.textout.insert(END, str(self.serial) + ": monkey killed! \n")
                self.textout.update()
                self.raw_cmd('pull', '/mnt/sdcard/monkeylog.log', './' + self.serial + '_monkeylog.log')
                time.sleep(1)
        except Exception, e:
            # self.textout.insert(END, "出错了\n")
            # self.textout.update()
            import traceback
            traceback.print_exc()

    def killmonkey_nohint(self):
        try:
            serial = self.getAdb2()
            for i in xrange(0, len(serial)):
                self.serial = serial[i]
                out = self.raw_cmd('shell', '/data/local/tmp/busybox ps | grep commands.monkey | grep -v "grep"')
                for i in out.split("\n"):
                    if " " in i:
                        ps = Popen("adb  -s " + self.serial + " shell kill " + i.split()[0], shell=True, stdout=PIPE,
                                   stderr=PIPE)
                        ps.communicate()

                out = self.raw_cmd('shell', '/data/local/tmp/busybox ps | grep AndroidJUnitRunner | grep -v "grep"')
                for i in out.split("\n"):
                    if " " in i:
                        ps = Popen("adb  -s " + self.serial + " shell kill " + i.split()[0], shell=True, stdout=PIPE,
                                   stderr=PIPE)
                        ps.communicate()
                self.textout.insert(END, str(self.serial) + ": monkey killed! \n")
                self.textout.update()
                self.raw_cmd('pull', '/mnt/sdcard/monkeylog.log', './' + self.serial + '_monkeylog.log')
                time.sleep(1)
        except Exception, e:
            # self.textout.insert(END, "出错了\n")
            # self.textout.update()
            import traceback
            traceback.print_exc()

    def killlc(self):
        try:
            serial = [self.serial]
            if tkinter.messagebox.askokcancel('提示', '停止所有设备点<是>,<否>仅仅停止选择的设备'):
                serial = self.getAdb2()
            else:
                pass
            for i in xrange(0, len(serial)):
                self.serial = serial[i]
                out = self.raw_cmd('shell', '/data/local/tmp/busybox ps | grep AndroidJUnitRunner | grep -v "grep"')
                for i in out.split("\n"):
                    if " " in i:
                        ps = Popen("adb  -s " + self.serial + " shell kill " + i.split()[0], shell=True, stdout=PIPE,
                                   stderr=PIPE)
                        ps.communicate()
                self.textout.insert(END, str(self.serial) + ": lc killed! \n")
                self.textout.update()
        except Exception, e:
            # self.textout.insert(END, "出错了\n")
            # self.textout.update()
            import traceback
            traceback.print_exc()

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
            self.textout.insert(END, "Click Point: " + xy + " , please wait...\n")
            self.textout.update()
            appdev = MinicapMin.TestDevice(serial=self.serial)
            appstarttime = appdev.testAppStartTime(int(self.screensave), xy)
        except Exception, e:
            self.textout.insert(END, "出错了\n")
            self.textout.update()
            import traceback
            traceback.print_exc()
        finally:
            self.textout.insert("5.0", "Test Minicap End!\n ")
            self.textout.update()

    def gettest(self):
        try:
            self.screensave = int(self.numberChosen.get())
            zhixingfangshi = self.radionButton_rp_value.get()
            if zhixingfangshi == "r":
                self.record()
            else:
                self.testFPS()
        except Exception, e:
            pass
            # import traceback
            # traceback.print_exc()
            #

    def record(self):
        self.textout.delete(1.0, END)
        ref = self.fileEdit.get()

        if ref == "":
            ref = os.getcwd() + "/temp.txt"
        self.textout.insert("1.0", "Record to file:" + ref)
        self.textout.update()
        (path, shotname) = os.path.split(ref)
        cmd = "wait-for-device shell /data/local/tmp/eventrec /sdcard/" + shotname
        try:
            start = datetime.datetime.now()
            process = subprocess.Popen(['adb', '-s', [self.serial], [cmd]])
            while process.poll() is None:
                time.sleep(2)
                now = datetime.datetime.now()
                if (now - start).seconds > int(self.screensave):
                    os.kill(process.pid, signal.SIGTERM)
                    return None
        except KeyboardInterrupt:
            print "Stop:", shotname
        finally:
            self.raw_cmd('pull', '/sdcard/' + shotname, os.getcwd())  # visual_bars
            self.textout.delete(1.0, END)
            self.textout.insert("1.0", "Save to File:" + ref)
            self.textout.update()

    def replay(self, pf):
        start = datetime.datetime.now()
        (path, shotname) = os.path.split(pf)
        if path == "":
            self.raw_cmd('push', os.getcwd() + '/' + pf, '/sdcard/')
        else:
            self.raw_cmd('push', pf, '/sdcard/')
        cmd = "shell /data/local/tmp/eventrec -p /sdcard/" + shotname
        process = subprocess.Popen(['adb', '-s', [self.serial], [cmd]])

        while process.poll() is None:
            time.sleep(2)
            now = datetime.datetime.now()
            du = now - start
            if du.seconds > 600:
                try:
                    process.terminate()
                    return True
                except Exception, e:
                    self.textout.insert(END, "出错了\n")
                    self.textout.update()
                    return False

    def grantPermission(self, pkg):
        "dumpsys package com.ape.filemanager | grep granted=false"
        self.raw_cmd('shell', 'pm', 'grant', pkg,
                     "android.permission.ACCESS_COARSE_LOCATION")
        self.raw_cmd('shell', 'pm', 'grant', pkg,
                     "android.permission.READ_EXTERNAL_STORAGE")
        self.raw_cmd('shell', 'pm', 'grant', pkg,
                     "android.permission.WRITE_EXTERNAL_STORAGE")
        self.raw_cmd('shell', 'pm', 'grant', pkg,
                     "android.permission.READ_CONTACTS")
        self.raw_cmd('shell', 'pm', 'grant', pkg,
                     "android.permission.WRITE_CONTACTS")
        self.raw_cmd('shell', 'pm', 'grant', pkg,
                     "android.permission.CALL_PHONE")
        self.raw_cmd('shell', 'pm', 'grant', pkg,
                     "android.permission.RECORD_AUDIO")
        self.raw_cmd('shell', 'pm', 'grant', pkg,
                     "android.permission.READ_PHONE_STATE")
        out = \
            self.raw_cmd('shell', 'dumpsys', 'package', pkg,
                         '| grep granted=false |cut -d \':\' -f 1')
        if "permission" in out:
            b = out.strip().split("\r")
            for i in b:
                self.raw_cmd('shell', 'pm', 'grant', pkg, i)

    def calcufps(self, pkg):
        fps = 0
        result = self.gtest(pkg)
        if (result[0] > 0) & (result[2] > 0):
            fps = result[2]
        return fps

    def parser_test_case(self, file):
        import json
        try:
            if ".json" not in file:
                print "no json test case file!"
                return 0
            with open(file, 'r') as load_f:
                jf = json.load(load_f)
                return jf
        except Exception, e:
            pass

    def platformRun2(self):
        if tkinter.messagebox.askokcancel('提示', '要执行GO整机测试吗？'):
            import ConfigParser
            import glob
            import csv
            self.inidevice()
            self.textout.delete(1.0, END)
            self.textout.insert(END, "GO is runing...\n")
            self.textout.insert(END, "系统：" + self.buildversion + "\n")
            self.textout.insert(END, "-" * 48 + "\n")
            self.textout.update()

            persistentmem = 0

            persistent = self.raw_cmd('shell', 'dumpsys', 'meminfo', '| grep -A 10 Persistent ')

            if "Persistent" in persistent:
                persistentmem = persistent.split(":")[0]
                if "K" in persistentmem:
                    persistentmem = persistentmem.replace("K", "")
                if "," in persistentmem:
                    persistentmem = persistentmem.replace(",", "")
                    persistentmem = int(persistentmem) / 1024
            print "" + persistent
            memAv = self.raw_cmd('shell', 'cat', '/proc/meminfo', '|grep MemAvailable')
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
                    writer.writerow(
                        ["Persistent", str(persistentmem), "MemAvailable", str(memAv) + " MB", "BuildVersion:",
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
                    version, buildversion, targetSDK = self.getAPKVersion()
                    self.grantPermission(pkg)

                    try:
                        for i in xrange(1, int(self.screensave) + 1):
                            print filename, u" 执行 %i 次..." % i
                            self.raw_cmd('shell', 'input', 'keyevent', '4')
                            time.sleep(0.1)
                            self.raw_cmd('shell', 'input', 'keyevent', '4')
                            time.sleep(0.1)
                            self.raw_cmd('shell', 'input', 'keyevent', '3')
                            time.sleep(0.1)
                            (path, shotname) = os.path.split(filename)
                            self.textout.insert(END, "<" + str(i) + "> 执行文件:" + str(shotname) + "\n")
                            self.textout.update()
                            out = self.raw_cmd('shell', 'am', 'start  -S -W', pkg + '/' + acv,
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
                                                self.raw_cmd('shell', ' input', 'tap',
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
                                self.swiptDown(None)
                                self.swiptUp(None)
                                fps.append(self.calcufps(pkg))
                            elif "ialer" in pkg:
                                self.swiptDown(None)
                                self.swiptUp(None)
                                fps.append(self.calcufps(pkg))
                            elif "alculator" in pkg:
                                self.swiptUp(None)
                                self.swiptDown(None)
                                fps.append(self.calcufps(pkg))
                            else:
                                self.swiptDown(None)
                                self.swiptUp(None)
                                fps.append(self.calcufps(pkg))

                            print u"第" + str(i) + u"次<" + pkg + ">" + u"帧速FPS: " + str(fps_avg) + u" 启动时间：" + str(
                                starttime_avg)

                            self.raw_cmd('shell', 'input', 'keyevent', '4')
                            time.sleep(0.1)
                            self.raw_cmd('shell', 'input', 'keyevent', '4')
                            time.sleep(0.1)
                            self.raw_cmd('shell', 'input', 'keyevent', '3')
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
                        self.textout.insert(END, "-" * 48 + "\n")
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
                        self.raw_cmd('shell', 'am', 'force-stop', pkg)
                        # self.getLog(pkg)
            except Exception, e:
                self.textout.insert(END, "platformRun2()出错了\n")
                self.textout.update()
                # import traceback
                # traceback.print_exc()
            finally:
                self.textout.insert(END, "-" * 48 + "\n")
                self.textout.insert(END, "测试完成\n")
                self.textout.update()

    def killsh(self):
        ps_line = self.raw_cmd('shell', 'cat', '/data/local/tmp/FPS.pid')
        if len(ps_line) > 0:
            pid = ps_line.strip()
            self.raw_cmd('shell', 'kill', str(pid))
        time.sleep(1)

    def get_battery(self):
        output = self.raw_cmd('shell', 'dumpsys battery')
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
            self.textout.insert(END, "Error!\n")
            self.textout.update()

    def cpuThreading(self):
        cpu = 0
        mem = 0
        try:
            while self.cpu_flag:
                time.sleep(2)
                pkg = self.getPackage()
                cmd = "shell top -n 1 | grep %s" % (pkg[:13])
                process = subprocess.Popen(['adb', '-s', [self.serial], [cmd]], stdout=PIPE, stderr=PIPE)
                output = process.stdout.readline()
                mem = int(float(self.getMemInfo(pkg)))
                if pkg[:13] in output:
                    sdkout = self.raw_cmd('shell', 'getprop', 'ro.build.version.sdk')
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
            self.textout.insert(END, "Error!\n")
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

    def dumnode(self, serial):
        try:
            allmd5 = ""
            xy = {}
            nodehas = []
            canbeclick = ["android.widget.Button", "android.widget.TextView", "android.widget.ImageButton",
                          "android.widget.ImageView", "android.widget.CompoundButton"]
            cannotbeclick = ["USB tethering", "reset", "RESET", "Factory data reset", "Start now", "Navigate up",
                             "USB connected, check to tether"]

            p = subprocess.Popen(['adb', '-s', serial, 'shell', '/system/bin/uiautomator ', 'dump', '--compressed',
                                  '/sdcard/gfxtest.xml'], stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
            time.sleep(0.2)
            xmldata = \
                subprocess.Popen(['adb', '-s', serial, 'shell', 'cat', '/sdcard/gfxtest.xml'], stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE).communicate()[0]
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

    def travel_thread(self):
        serial = [self.serial]
        if tkinter.messagebox.askokcancel('提示', '运行所有设备点<是>,<否>仅仅执行选择的设备'):
            serial = self.getAdb2()
        else:
            pass
        for i in xrange(0, len(serial)):
            self.serial = serial[i]
            self.textout.insert(END, self.serial + " run travel at: " + str(
                datetime.datetime.now().strftime("%m/%d-%H:%M:%S")) + " \n")
            self.textout.update()
            allpkg = []
            out = self.raw_cmd('shell', "pm list package |grep -E '(ape.)|(myos.)|(com.a)'")
            for k in (out.strip().split("\r")):
                pkg = k[k.find("package:") + 8:]
                allpkg.append(pkg)
            t = threading.Thread(target=self.travel2, args=(allpkg, self.serial))
            t.setDaemon(True)
            t.start()

    def travel2(self, pkgs, serial):
        try:
            for i in xrange(1, int(self.screensave) + 1):
                print "travel times:", i
                for pkg in pkgs:
                    clicklist = {}
                    blacklist = {}
                    nomd, xy, an = self.dumnode(serial)
                    perkey = []
                    runtflat = True
                    print "trave app:", pkg
                    while ("packageinstaller" in an) or ("android:id/alertTitle" in an):
                        for p in xrange(6):
                            for pi in xy.keys():
                                perkey.append(xy.get(pi))
                        self.permissionClick(max(perkey), serial)
                        nomd, xy, an = self.dumnode(serial)

                    base = xy
                    nomdo = nomd
                    ct = 0
                    timeNow = time.time()
                    packagenow = pkg
                    while ct <= int(590) and (len(xy) > 0) and runtflat:
                        ct = time.time() - timeNow
                        print "serial time:", serial, ct
                        ky = xy.keys()[random.randint(0, len(xy) - 1)]
                        cxy = xy.pop(ky)
                        if ky not in blacklist:
                            if ky in clicklist:
                                clicklist[ky] += 1
                            else:
                                clicklist[ky] = 1
                            if (clicklist[ky]) < 10:
                                self.raw_cmd('shell', ' input', 'tap', str(cxy[0]),
                                             str(cxy[1]))
                                subprocess.Popen(['adb', '-s', serial, 'shell', 'input', 'tap', str(cxy[0]),
                                                  str(cxy[1])], stdout=subprocess.PIPE,
                                                 stderr=subprocess.PIPE).communicate()
                            packagenow = self.getPackage()
                            if pkg not in packagenow:
                                blacklist[ky] = cxy
                                if pkg != "":
                                    subprocess.Popen(['adb', '-s', serial, 'shell', 'am', 'force-stop', pkg],
                                                     stdout=subprocess.PIPE,
                                                     stderr=subprocess.PIPE).communicate()
                                subprocess.Popen(['adb', '-s', serial, 'shell', 'input', 'keyevent', '3'],
                                                 stdout=subprocess.PIPE,
                                                 stderr=subprocess.PIPE).communicate()
                                subprocess.Popen(['adb', '-s', serial, 'shell', 'monkey', '-p', pkg, '-c',
                                                  'android.intent.category.LAUNCHER', '1'],
                                                 stdout=subprocess.PIPE,
                                                 stderr=subprocess.PIPE).communicate()
                            time.sleep(1)
                            nomdn, xy, an = self.dumnode(serial)
                            if nomdn == nomdo:
                                blacklist[ky] = cxy
                                continue
                            else:
                                nomdo = nomdn
                        inter = dict.fromkeys([x for x in base if x in blacklist])
                        df = list(set(base.keys()).difference(set(inter.keys())))
                        if df == []:
                            # print  pkg + "-->over!"
                            break
                        elif len(xy) == 0:
                            if pkg != "":
                                subprocess.Popen(['adb', '-s', serial, 'shell', 'am', 'force-stop', pkg],
                                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                            time.sleep(0.2)
                            subprocess.Popen(['adb', '-s', serial, 'shell', 'monkey', '-p', pkg, '-c',
                                              'android.intent.category.LAUNCHER', '1'],
                                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                            time.sleep(1)
                            nomdn, xy, an = self.dumnode(serial)
                            runtflat = False
                            subprocess.Popen(['adb', '-s', serial, 'shell', 'input', 'keyevent', '4'],
                                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                            subprocess.Popen(['adb', '-s', serial, 'shell', 'input', 'keyevent', '3'],
                                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                            print  pkg + "-->End!"
        except Exception, e:
            self.cpu_flag = False
            import traceback
            traceback.print_exc()
            self.textout.insert(END, "出错了\n")
            self.textout.update()
        finally:
            self.cpu_flag = False

    def permissionClick(self, xy, serial):
        subprocess.call('adb -s ' + serial + " wait-for-device shell input tap " + str(xy[0]) + " " + str(xy[1]))
        time.sleep(0.2)
        print "permission click:", xy

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
            out = self.raw_cmd('shell', 'getevent -p  | grep -B 15 \"0035\"')
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

    def playatxthread(self, playfile, rt, ct):
        if ".txt" in playfile:
            t = threading.Thread(target=self.playatxfile, args=(playfile, rt, ct,))
            t.setDaemon(True)
            t.start()
            t.join()
        elif ".json" in playfile:
            tcs = self.parser_test_case(playfile)
            t = threading.Thread(target=self.playatxfile, args=(tcs, rt, ct,))
            t.setDaemon(True)
            t.start()
            t.join()

    def playatxfile(self, playfile, rtime, count):
        try:
            reporttime = rtime
            serial_b = None
            if type(playfile) == dict:
                for i in playfile["Testcases"]:
                    print "json play:", i
                    self.logger.debug("TestCaseID:" + str(i["ID"]))
                    self.stepresult.append(
                        [[{'TotalResult': True, 'ResportName': reporttime, 'TestFileName': str(i["ID"]),
                           'Times': int(self.screensave)}], []])
                    with open(i["URL"], 'a+') as f:
                        lines = f.read()
                        readline = lines.split("\n")
                        for j, val in enumerate(readline):
                            if "@" in val:
                                device_b = Device(val.split("@")[0])
                                break
                    self.textout.insert(1.0, "_" * 48 + "\n")
                    self.textout.insert(1.0, "[" + str(count) + "] Start TC: " + str(i["ID"]) + " \n")
                    rt = self.playatxcontent(readline, serial_b, reporttime)
                    self.logger.debug(
                        "[" + str(count) + "] End: " + ("Pass" if self.stepresult[-1][0][0]['TotalResult'] else "Fail"))
                    # self.textout.insert(1.0, "_" * 48 + "\n")
                    self.textout.insert(1.0, "[" + str(count) + "] End & Result " + (
                        "Pass" if self.stepresult[-1][0][0]['TotalResult'] else "Fail") + "\n")
            elif ".txt" in playfile:
                with open(playfile, 'a+') as f:
                    lines = f.read()
                    readline = lines.split("\n")
                    try:
                        print "playfile:", playfile
                        casename = os.path.splitext(os.path.split(playfile)[1])[0]
                        print "casename:", casename
                    except Exception, e:
                        casename = playfile
                    for i, val in enumerate(readline):
                        if "@" in val:
                            serial_b = val.split("@")[0]
                            break
                self.stepresult.append(
                    [[{'TotalResult': True, 'ResportName': reporttime, 'TestFileName': casename.encode('utf-8'),
                       'Times': int(self.screensave)}], []])
                self.textout.insert(1.0, "[" + str(count) + "] Start TC: " + casename + " \n")
                rt = self.playatxcontent(readline, serial_b, reporttime)
                self.logger.debug("[" + str(count) + "] End TC: " + casename.encode('utf-8') + (
                    ": Pass" if self.stepresult[-1][0][0]['TotalResult'] else ":Fail"))
                # self.textout.insert(1.0, "_" * 48 + "\n")
                # print "step result:", self.stepresult
                self.textout.insert(1.0, "[" + str(count) + "] End & Result: " + (
                    "Pass" if self.stepresult[-1][0][0]['TotalResult'] else "Fail") + "\n")
                self.textout.update()

        except Exception, e:
            import traceback
            traceback.print_exc()
            self.textout.insert(END, "控制出错了\n")
            self.textout.update()

        finally:
            pass

    def playatxcontent(self, playcontent, sb=None, reporttime=""):
        playscreenx = self.WIDTH
        playscreeny = self.HEIGHT
        restricscreen = self.getShape()
        resx = restricscreen[0]
        resy = restricscreen[1]
        serial = self.serial
        op = ""
        serial_b = sb
        loopflag = False
        sub_content = []
        sub_content_times = 0
        device = {serial: Device(serial), serial_b: None}
        device_m = {serial: DeviceMixin(device[serial]), serial_b: None}
        device_s = {serial: [self.WIDTH, self.HEIGHT], serial_b: [None, None]}
        if serial_b != None:
            if not self.installbundleonB:
                self.installbundle(serial_b)
                installbundleonB = True
                device[serial_b] = Device(serial_b)
                device_m[serial_b] = DeviceMixin(device[serial_b])
                size = self.screenSize(serial_b)
                device_s[serial_b] = [int(size[0]), int(size[1])]
        try:
            for index, line in enumerate(playcontent):
                if line != "":

                    if "@" in line:
                        serial = line.split("@")[0]
                        # threading.Thread(target=self.device_info_thread, args=(self.serial,)).start()
                        time.sleep(1)
                        self.d = device[serial]
                        # self.dm = device_m[serial]
                        line = line.split("@")[1]
                    else:
                        serial = self.serial
                        self.d = device[serial]
                        # self.dm = device_m[serial]
                    if loopflag and "end" not in line:
                        sub_content.append(line)
                        continue
                    elif loopflag and "end" in line:
                        loopflag = False
                        for i in xrange(0, sub_content_times):
                            self.playatxcontent(sub_content, sb=None)

                    elif "display:" in line:
                        playscreenx = int(line.split(":")[1].split("_")[0])
                        playscreeny = int(line.split(":")[1].split("_")[1])
                    elif "screenon:" in line:
                        par = line.split(":")[1]
                        if par == "on":
                            if self.d.screen == "on":  # of self.d.screen != "off"
                                # do something in case of screen on
                                pass
                            if self.d.screen == "off":  # of self.d.screen != "on"
                                self.d.wakeup()
                        elif par == "off":
                            if self.d.screen == "on":  # of self.d.screen != "off"
                                # do something in case of screen on
                                self.d.sleep()
                            if self.d.screen == "off":  # of self.d.screen != "on"
                                pass
                    elif "clickscreen" in line:
                        op = "clickscreen"
                        par = line.split(":")[1]
                        x = int(par.split("x")[0])
                        y = int(par.split("x")[1])
                        print "clickscreen:", x, y
                        if playscreenx > device_s[serial][0]:
                            x = int(x) * playscreenx / device_s[serial][0]
                        else:
                            x = int(x) * device_s[serial][0] / playscreenx
                        if playscreeny > device_s[serial][1]:
                            y = int(y) * playscreeny / device_s[serial][1]
                        else:
                            y = int(y) * device_s[serial][1] / playscreeny
                        # print int(x),int(y),resx,resy
                        if int(y) > int(resy):
                            if (int(x)) < device_s[serial][0] / 3:
                                self.d.press.back()
                                time.sleep(0.5)
                            elif (int(x)) > device_s[serial][0] * 0.7:
                                self.d.press.recent()
                                time.sleep(1)
                            else:
                                self.d.press.home()
                                time.sleep(0.5)

                        else:
                            if "long" in line:
                                self.d.long_click(x, y)
                            else:
                                self.d.click(x, y)
                            time.sleep(0.5)
                    elif "drag:" in line or "swipe:" in line:
                        op = "drag"
                        par = line.split(":")[1]
                        x = float(par.split(",")[0])
                        y = float(par.split(",")[1])
                        x1 = float(par.split(",")[2])
                        y1 = float(par.split(",")[3])

                        if playscreenx > device_s[serial][0]:
                            x = float(x) * playscreenx / device_s[serial][0]
                            x1 = float(x1) * playscreenx / device_s[serial][0]
                        else:
                            x = float(x) * device_s[serial][0] / playscreenx
                            x1 = float(x1) * device_s[serial][0] / playscreenx
                        if playscreeny > device_s[serial][1]:
                            y = float(y) * playscreeny / device_s[serial][1]
                            y1 = float(y1) * playscreeny / device_s[serial][1]
                        else:
                            y = float(y) * device_s[serial][1] / playscreeny
                            y1 = float(y1) * playscreeny / device_s[serial][1]
                        if "drag" in line:
                            result = self.d.drag(x, y, x1, y1, 30)
                        else:
                            result = self.d.swipe(x, y, x1, y1, 30)
                        time.sleep(1)
                    elif "takeshot" in line:
                        self.d.screenshot(
                            "pic/takeshot_" + time.strftime("%m%d%H%M%S", time.localtime()) + ".png", scale=0.5,
                            quality=50)

                    elif "checktext" in line:
                        wtimeout = 5
                        if "," in line:
                            wtimeout = int(line.split(",")[1])
                            line = line.split(",")[0]
                        x = line.split(":")[1]
                        try:
                            p = self.d(text=x).wait.exists(timeout=wtimeout * 2000)
                        except Exception, e:
                            continue
                        imgsrc = self.minicap_ins.crop_image()
                        if imgsrc == None:
                            continue
                        # imgsrc = Image.open(self.d.screenshot("tmp.png"))
                        if p:
                            self.textout.insert(1.0, " ." + str(index) + ". " + serial + " Check Text:" + x + " Pass\n")
                            self.logger.info(str(index) + " " + serial + " Check Text:" + x + " Pass")
                            try:
                                b = self.d(text=x).bounds
                                box = [b["left"], b["top"], b["right"], b["bottom"]]
                                if int(self.WIDTH) > 360:
                                    b0 = int(box[0] * 360.0 / self.WIDTH)
                                    b2 = int(box[2] * 360.0 / self.WIDTH)
                                else:
                                    b0 = int(box[0] * self.WIDTH / 360.0)
                                    b2 = int(box[2] * self.WIDTH / 360.0)
                                if int(self.HEIGHT) > 720:
                                    b1 = int(box[1] * 720.0 / self.HEIGHT)
                                    b3 = int(box[3] * 720.0 / self.HEIGHT)
                                else:
                                    b1 = int(box[1] * 720.0 / self.HEIGHT)
                                    b3 = int(box[3] * self.HEIGHT / 720.0)
                                # pink = self.canvas.create_rectangle([b0, b1, b2, b3], outline='red', width=3,
                                #                                     tags='pink')
                                # time.sleep(2)
                                # self.draw_step_threading([b0, b1, b2, b3])
                                # time.sleep(0.2)
                                draw = ImageDraw.Draw(imgsrc)
                                draw.rectangle(box, outline="pink")
                                draw.rectangle((box[0] - 1, box[1] - 1, box[2] - 1, box[3] - 1), outline="pink")
                                draw.rectangle((box[0] - 2, box[1] - 2, box[2] - 2, box[3] - 2), outline="pink")
                                draw.text((20, self.HEIGHT * 0.3), str(index) + ". CheckText:" + x + " Pass", 'fuchsia',
                                          self.drawfont)
                                picname = os.getcwd() + "/pic/" + reporttime + "/" + time.strftime("%m%d%H%M%S",
                                                                                                   time.localtime()) + "_" + str(
                                    index) + "_CheckText_Pass.png"
                                if imgsrc == None:
                                    return
                                elif imgsrc.size[0] < 10:
                                    return
                                imgsrc.thumbnail((imgsrc.size[0] * 0.4, imgsrc.size[1] * 0.4), Image.ANTIALIAS)
                                imgsrc.save(picname)
                                ##self.showandclosep_threading(picname)
                                self.stepresult[-1][1].append(
                                    {"step": index, "tcs": " Check Text:" + x, "result": "Pass", "url": picname})

                            except Exception, e:
                                self.stepresult[-1][0][0]['TotalResult'] = False
                                self.stepresult[-1][1].append(
                                    {"step": index, "tcs": " Check Text:" + x, "result": "Fail", "url": picname})
                                continue
                        else:
                            self.logger.error(str(index) + " " + serial + " Check Text:" + x + " Fail! ")
                            self.textout.insert(1.0, " ." + str(index) + ". " + serial + " Check Text:" + x + " Fail\n")
                            draw = ImageDraw.Draw(imgsrc)
                            draw.text((20, self.HEIGHT * 0.3), str(index) + ". CheckText:" + x + " Fail", 'fuchsia',
                                      self.drawfont)
                            picname = os.getcwd() + "/pic/" + reporttime + "/" + time.strftime("%m%d%H%M%S",
                                                                                               time.localtime()) + "_" + str(
                                index) + "_CheckText_Fail.png"
                            if imgsrc == None:
                                return
                            elif imgsrc.size[0] < 10:
                                return
                            imgsrc.thumbnail((imgsrc.size[0] * 0.4, imgsrc.size[1] * 0.4), Image.ANTIALIAS)
                            imgsrc.save(picname)
                            # self.showandclosep_threading(picname)
                            self.stepresult[-1][0][0]['TotalResult'] = False
                            self.stepresult[-1][1].append(
                                {"step": index, "tcs": " Check Text:" + x, "result": "Fail", "url": picname})


                    elif "checkimage" in line:
                        wtimeout = 10
                        if "," in line:
                            wtimeout = int(line.split(",")[1])
                            line = line.split(",")[0]
                        x = line[line.find(":") + 1:]
                        (path, shotname) = os.path.split(x)
                        (fn, typbc) = os.path.splitext(shotname)
                        # if not os.path.exists(path + "/" + fn+ ".tmp.png"):
                        if "." in fn and "x" in fn:
                            reselution = fn.split(".")[1]
                            irx = float(reselution.split("x")[0])
                            iry = float(reselution.split("x")[1])
                            if irx != int(device_s[serial][0]) or iry != int(device_s[serial][1]):
                                x1 = path + "/" + fn + "_" + str(device_s[serial][0]) + "x" + str(
                                    device_s[serial][1]) + ".png"
                                if not os.path.exists(x1):
                                    img = Image.open(x.decode("utf8"))
                                    w, h = img.size
                                    w = w / (irx / float(device_s[serial][0])) if irx > float(
                                        device_s[serial][0]) else w * (
                                        float(device_s[serial][0]) / irx)
                                    h = h / (iry / float(device_s[serial][1])) if iry > float(
                                        device_s[serial][1]) else h * (
                                        float(device_s[serial][1]) / iry)
                                    img = img.resize((int(w), int(h)), Image.ANTIALIAS)
                                    img.save(x1.decode('utf-8').strip())
                                    print "checkimage open"
                                getORno = self.find_template(img=x1, wt=wtimeout)
                            else:
                                getORno = self.find_template(img=x, wt=wtimeout)
                        print "checkimage:" + str(x) + "-->" + str(getORno)
                        imgsrc = self.minicap_ins.crop_image()
                        if imgsrc == None:
                            continue
                        # self.cavas_step_threading(x)
                        # imgsrc = Image.open(self.d.screenshot("tmp.png"))
                        draw = ImageDraw.Draw(imgsrc)
                        if getORno == None:
                            self.textout.insert(1.0,
                                                " ." + str(index) + ". " + serial + " Check Image:" + fn.split(".")[
                                                    0] + " Fail\n")
                            self.logger.error(
                                str(index) + " " + serial + " Check Image:" + fn.split(".")[0] + " Fail! ")
                            draw.text((20, self.HEIGHT * 0.3),
                                      str(index) + ". CheckImage:" + fn.split(".")[0] + " Fail",
                                      'fuchsia', self.drawfont)
                            picname = os.getcwd() + "/pic/" + reporttime + "/" + time.strftime("%m%d%H%M%S",
                                                                                               time.localtime()) + "_" + str(
                                index) + "_CheckImage_Fail.png"
                            if imgsrc == None:
                                return
                            elif imgsrc.size[0] < 10:
                                return
                            imgsrc.thumbnail((imgsrc.size[0] * 0.4, imgsrc.size[1] * 0.4), Image.ANTIALIAS)
                            imgsrc.save(picname)
                            # self.showandclosep_threading(picname)
                            self.stepresult[-1][0][0]['TotalResult'] = False
                            self.stepresult[-1][1].append(
                                {"step": index, "tcs": "Check Image:" + fn.split(".")[0], "result": "Fail",
                                 "url": x, "url2": picname})
                        else:
                            xy_x = getORno[0]
                            xy_y = getORno[1]
                            xy_x1 = getORno[2]
                            xy_y1 = getORno[3]
                            if int(self.WIDTH) > 360:
                                xy_x_r = int(xy_x * 360.0 / self.WIDTH)
                                xy_x1_r = int(xy_x1 * 360.0 / self.WIDTH)
                            else:
                                xy_x_r = int(xy_x * self.WIDTH / 360.0)
                                xy_x1_r = int(xy_x1 * self.WIDTH / 360.0)
                            if int(self.HEIGHT) > 720:
                                xy_y_r = int(xy_y * 720.0 / self.HEIGHT)
                                xy_y1_r = int(xy_y1 * 720.0 / self.HEIGHT)
                            else:
                                xy_y_r = int(xy_y * self.HEIGHT / 720.0)
                                xy_y1_r = int(xy_y1 * self.HEIGHT / 720.0)
                            # drawline = self.canvas.create_line(0, 575, xy_x_r, xy_y1_r, fill="red", dash=(4, 4),width=3, arrow=tkinter.LAST)

                            # self.draw_step_threading([xy_x_r, xy_y_r, xy_x1_r, xy_y1_r])
                            # drawline = self.canvas.create_line(0, 120, xy_x_r, xy_y_r, fill="orange", dash=(4, 4), width=3,
                            #                                     arrow=tkinter.LAST,tags="box")
                            # orange = self.canvas.create_rectangle([xy_x_r, xy_y_r, xy_x1_r, xy_y1_r], outline='red',
                            #                                       width=3, tags="orange")
                            # time.sleep(1)
                            # self.canvas.delete(orange)
                            # print "line:", line, orange
                            # time.sleep(0.2)
                            self.logger.info(str(index) + " " + serial + " Check Image:" + fn.split(".")[0] + " Pass")
                            self.textout.insert(1.0,
                                                " ." + str(index) + ". " + serial + " Check Image:" + fn.split(".")[
                                                    0] + " Pass\n")
                            draw.rectangle((xy_x, xy_y, xy_x1, xy_y1), outline="orange")
                            draw.rectangle((xy_x - 1, xy_y - 1, xy_x1 - 1, xy_y1 - 1), outline="orange")
                            draw.rectangle((xy_x - 2, xy_y - 2, xy_x1 - 2, xy_y1 - 2), outline="orange")
                            draw.text((20, self.HEIGHT * 0.3),
                                      str(index) + ". CheckImage:" + fn.split(".")[0] + " Pass",
                                      'fuchsia', self.drawfont)
                            picname = os.getcwd() + "/pic/" + reporttime + "/" + time.strftime("%m%d%H%M%S",
                                                                                               time.localtime()) + "_" + str(
                                index) + "_CheckImage_Pass.png"
                            if imgsrc == None:
                                return
                            elif imgsrc.size[0] < 10:
                                return
                            imgsrc.thumbnail((imgsrc.size[0] * 0.4, imgsrc.size[1] * 0.4), Image.ANTIALIAS)
                            imgsrc.save(picname)
                            # self.showandclosep_threading(picname)
                            self.stepresult[-1][1].append(
                                {"step": index, "tcs": "Check Image:" + fn.split(".")[0], "result": "Pass",
                                 "url": x, "url2": picname})

                    elif "ocrtext" in line:
                        op = "ocrtext"
                        self.screenShot(os.getcwd())
                        x = line.split(":")[1]
                        result = MYOCRTest.repara()
                        print result
                        for i in xrange(len(result)):
                            if x[1:-1] in result[i].get("words"):
                                self.logger.info("<" + x + ">" + " < Found! >")
                                break
                            elif i == len(result) - 1:
                                self.logger.error("<" + x + ">" + " < Not Found! >")
                                self.d.screenshot(
                                    "pic/ocrtext_nf_" + time.strftime("%m%d%H%M%S", time.localtime()) + ".png",
                                    scale=0.5, quality=50)

                    elif "ocrface" in line:
                        print u"人脸识别"
                        MYOCRTest.repface()

                    elif line[0:4] == "inst":
                        print "install app"
                        x = line.split(":")[1]
                        result = self.install_thread(x)
                        self.logger.debug("install:" + x + ":" + result.strip())


                    elif line[0:4] == "unin":
                        print "uninstall app"
                        op = "uninstall"
                        x = line.split(":")[1]
                        result = self.raw_cmd('shell', 'pm', 'uninstall', x)
                        self.logger.debug("unininstall:" + x + ":" + result.strip())

                    elif "launch" in line:
                        print "launch app"
                        op = "launch"
                        x = line.split(":")[1]
                        result = self.raw_cmd('shell',
                                              'monkey', '-p', x, '-c', 'android.intent.category.LAUNCHER', '1')[
                                 0:8]
                        self.logger.debug("launch app:" + x + ":" + result.strip())


                    elif "sleep" in line:
                        if ":" in line:
                            x = line.split(":")[1]
                            time.sleep(float(x))
                        else:
                            time.sleep(1)

                    elif "pressback" in line:
                        if ":" in line:
                            x = line.split(":")[1]
                            for i in xrange(0, int(x)):
                                subprocess.Popen(['adb', '-s', serial, 'shell', 'input', 'keyevent', '4'],
                                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                                time.sleep(1)
                        else:
                            self.d.press.back()

                    elif "orientation" in line:

                        op = "orientation"
                        x = line.split(":")[1]
                        if "l" in x or "r" in x or "n" in x:
                            self.d.orientation = x

                    elif "reboot" in line:
                        self.raw_cmd('shell', 'reboot')
                        print "reboot....."
                        time.sleep(40)
                        out = self.raw_cmd('get-state')
                        print "reboot.....", out
                        if "device" in out:
                            print "reboot ok"

                    elif "shell" in line:  # input keyevent 66
                        op = "shellcmd"
                        x = line.split(":")[1]
                        self.raw_cmd('shell', x)

                    elif "presshome" in line:
                        subprocess.call('adb -s ' + serial + ' shell input keyevent 3')
                        time.sleep(1)
                        print "presshome"

                    elif "pressrecent" in line:
                        result = self.d.press.recent()
                    elif "loop:" in line:
                        loopflag = True
                        x = line.split(":")[1]
                        sub_content_times = int(x)

                    elif "clicktext" in line:
                        try:
                            x = line.split(":")[1]
                            picnameb = os.getcwd() + "/pic/" + reporttime + "/" + time.strftime("%m%d%H%M%S",
                                                                                                time.localtime()) + "_" + str(
                                index) + "_BeforClickText_" + x.decode('utf-8') + ".png"
                            b = self.d(text=x).bounds
                            box = (b["left"], b["top"], b["right"], b["bottom"])
                            # imgsrc =  Image.open(self.d.screenshot("tmp.png"))#
                            imgsrc = self.minicap_ins.crop_image()
                            if imgsrc == None:
                                continue
                            draw = ImageDraw.Draw(imgsrc)
                            draw.ellipse((box[0] + (box[2] - box[0]) / 2 - 15, box[1] + (box[3] - box[1]) / 2 - 15,
                                          box[0] + (box[2] - box[0]) / 2 + 15, box[1] + (box[3] - box[1]) / 2 + 15),
                                         fill=(255, 0, 0))
                            if imgsrc == None:
                                return
                            elif imgsrc.size[0] < 10:
                                return
                            imgsrc.thumbnail((imgsrc.size[0] * 0.4, imgsrc.size[1] * 0.4), Image.ANTIALIAS)
                            imgsrc.save(picnameb)
                            result = self.d(text=x).click()
                            picname = os.getcwd() + "/pic/" + reporttime + "/" + time.strftime("%m%d%H%M%S",
                                                                                               time.localtime()) + "_" + str(
                                index) + "_ClickText_" + ("Pass" if result else "Fail") + ".png"
                            self.textout.insert(1.0, " ." + str(index) + ". " + serial + " Click Text:" + x + " Pass\n")
                            self.logger.info(str(index) + " " + serial + " Click Text:" + x + " Pass")
                            self.stepresult[-1][1].append(
                                {"step": index, "tcs": "Click Text:" + x, "result": ("Pass" if result else "Fail"),
                                 "url": picnameb, "url2": picname})
                            time.sleep(2)

                            imgsrc = self.minicap_ins.crop_image()
                            if imgsrc == None:
                                return
                            elif imgsrc.size[0] < 10:
                                return
                            imgsrc.thumbnail((imgsrc.size[0] * 0.4, imgsrc.size[1] * 0.4), Image.ANTIALIAS)
                            imgsrc.save(picname)
                            # self.showandclosep_threading(picname)

                        except Exception, jc:
                            import traceback
                            traceback.print_exc()
                            self.logger.error(str(index) + " " + serial + " Click Text:" + x + " Fail")

                            picname = os.getcwd() + "/pic/" + reporttime + "/" + time.strftime("%m%d%H%M%S",
                                                                                               time.localtime()) + "_" + str(
                                index) + "_ClickText_Exception.png"
                            self.d.screenshot(picname, scale=0.5, quality=50)
                            self.stepresult[-1][0][0]['TotalResult'] = False
                            self.stepresult[-1][1].append(
                                {"step": index, "tcs": "Click Text:" + x, "result": "Fail",
                                 "url": picname, "url2": picnameb})
                            self.textout.insert(1.0, " ." + str(index) + ". " + serial + " Click Text:" + x + " Fail\n")
                            subprocess.Popen(['adb', '-s', serial, 'shell', 'input', 'keyevent', '4'],
                                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                            time.sleep(1)


                    elif "waitfortext" in line:
                        try:
                            x = line.split(":")[1]
                            wtimeout = 3
                            if "," in x:
                                wtext = x.split(",")[0]
                                wtimeout = int(x.split(",")[1])
                                self.d(text=wtext).wait.exists(timeout=wtimeout * 1000)
                                time.sleep(1)
                                self.logger.info("waitfortext:" + x)
                            else:
                                self.d(text=x).wait.exists(timeout=wtimeout * 1000)
                        except Exception, jc:
                            self.textout.insert(1.0, "等待文字出错：" + x + "\n")
                            subprocess.Popen(['adb', '-s', serial, 'shell', 'input', 'keyevent', '4'],
                                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                            time.sleep(1)
                            self.d.screenshot(
                                "pic/waitfortext_ERROR_" + time.strftime("%m%d%H%M%S", time.localtime()) + ".png",
                                scale=0.5, quality=50)



                    elif "playrecord" in line:
                        op = "playrecord"
                        x = line[line.find(":") + 1:]
                        result = self.replay(x)

                    elif "scrolltotext:" in line:
                        op = "scrolltotext"
                        x = line[line.find(":") + 1:]
                        result = self.d(scrollable=True).scroll.to(text=x)
                        self.d(text=x).click()
                        time.sleep(1)

                    elif "startapp:" in line:
                        op = "startapp"
                        x = line[line.find(":") + 1:]
                        self.raw_cmd('shell',
                                     'monkey', '-p', x, '-c', 'android.intent.category.LAUNCHER', '1')
                        time.sleep(2)
                        for i in xrange(0, 8):
                            if "packageinstaller" in self.getPackage():
                                self.d(className="android.widget.Button")[1].click()
                                time.sleep(0.5)
                            else:
                                break

                    elif "clickimage:" in line:
                        wtimeout = 10
                        getORno = None
                        if "," in line:
                            wtimeout = int(line.split(",")[1])
                            line = line.split(",")[0]
                        x = line[line.find(":") + 1:].decode("utf8")
                        (path, shotname) = os.path.split(x)
                        (fn, typbc) = os.path.splitext(shotname)
                        # self.cavas_step_threading(x)
                        if "." in fn and "x" in fn:
                            reselution = fn.split(".")[1]
                            irx = float(reselution.split("x")[0])
                            iry = float(reselution.split("x")[1])
                            if irx != int(device_s[serial][0]):
                                x1 = path + "/" + fn + "_" + str(device_s[serial][0]) + "x" + str(
                                    device_s[serial][1]) + ".png"
                                if not os.path.exists(x1):
                                    img = Image.open(x)
                                    w, h = img.size
                                    w = w / (irx / float(device_s[serial][0])) if irx > float(
                                        device_s[serial][0]) else w * (
                                        float(device_s[serial][0]) / irx)
                                    h = h / (iry / float(device_s[serial][1])) if iry > float(
                                        device_s[serial][1]) else h * (
                                        float(device_s[serial][1]) / iry)
                                    img = img.resize((int(w), int(h)), Image.ANTIALIAS)
                                    img.save(x1.strip())
                                getORno = self.find_template(img=x1, wt=wtimeout)
                            else:
                                getORno = self.find_template(img=x, wt=wtimeout)

                        imgsrc = self.minicap_ins.crop_image()
                        if imgsrc == None:
                            continue
                        # imgsrc = Image.open(self.d.screenshot("tmp.png"))
                        draw = ImageDraw.Draw(imgsrc)
                        if getORno == None:
                            self.textout.insert(1.0,
                                                " ." + str(index) + ". " + serial + " Click Image:" + fn.split(".")[
                                                    0] + " Fail\n")
                            self.logger.error(str(index) + " " + serial + " Click Image:" + fn.split(".")[0] + " Fail")
                            draw.text((20, self.HEIGHT * 0.3),
                                      str(index) + ". ClickImage:" + fn.split(".")[0] + " Fail",
                                      'fuchsia', self.drawfont)
                            picname = os.getcwd() + "/pic/" + reporttime + "/" + time.strftime("%m%d%H%M%S",
                                                                                               time.localtime()) + "_" + str(
                                index) + "_ClickImage_Fail.png"
                            if imgsrc == None:
                                return
                            elif imgsrc.size[0] < 10:
                                return
                            imgsrc.thumbnail((imgsrc.size[0] * 0.4, imgsrc.size[1] * 0.4), Image.ANTIALIAS)
                            imgsrc.save(picname)
                            # self.showandclosep_threading(picname)
                            self.stepresult[-1][0][0]['TotalResult'] = False
                            self.stepresult[-1][1].append(
                                {"step": index, "tcs": "Click Image:" + fn.split(".")[0], "result": "Fail",
                                 "url": x, "url2": picname})
                        else:
                            xy_x = getORno[0]
                            xy_y = getORno[1]
                            xy_x1 = getORno[2]
                            xy_y1 = getORno[3]
                            if int(self.WIDTH) > 360:
                                xy_x_r = int(xy_x * 360.0 / self.WIDTH)
                                xy_x1_r = int(xy_x1 * 360.0 / self.WIDTH)
                            else:
                                xy_x_r = int(xy_x * self.WIDTH / 360.0)
                                xy_x1_r = int(xy_x1 * self.WIDTH / 360.0)
                            if int(self.HEIGHT) > 720:
                                xy_y_r = int(xy_y * 720.0 / self.HEIGHT)
                                xy_y1_r = int(xy_y1 * 720.0 / self.HEIGHT)
                            else:
                                xy_y_r = int(xy_y * self.HEIGHT / 720.0)
                                xy_y1_r = int(xy_y1 * self.HEIGHT / 720.0)
                            # self.draw_step_threading([xy_x_r, xy_y_r, xy_x1_r, xy_y1_r])
                            # drawline = self.canvas.create_line(0, 120, xy_x_r, xy_y_r, fill="orange", dash=(4, 4), width=3,
                            #                                    arrow=tkinter.LAST, tags="box")
                            # red = self.canvas.create_rectangle([xy_x_r, xy_y_r, xy_x1_r, xy_y1_r], outline='red',
                            #                                    width=3, tags="red")
                            # time.sleep(1)
                            draw.rectangle((xy_x, xy_y, xy_x1, xy_y1), outline="red")
                            draw.rectangle((xy_x - 1, xy_y - 1, xy_x1 - 1, xy_y1 - 1), outline="red")
                            draw.rectangle((xy_x - 2, xy_y - 2, xy_x1 - 2, xy_y1 - 2), outline="red")
                            draw.text((20, self.HEIGHT * 0.3),
                                      str(index) + ". ClickImage:" + fn.split(".")[0] + " Pass",
                                      'fuchsia', self.drawfont)
                            picname = os.getcwd() + "/pic/" + reporttime + "/" + time.strftime("%m%d%H%M%S",
                                                                                               time.localtime()) + "_" + str(
                                index) + "_ClickImage_Pass.png"
                            if imgsrc == None:
                                return
                            elif imgsrc.size[0] < 10:
                                return
                            imgsrc.thumbnail((imgsrc.size[0] * 0.4, imgsrc.size[1] * 0.4), Image.ANTIALIAS)
                            imgsrc.save(picname)
                            # self.stepresult[-1][0][0]['TotalResult'] = True
                            print "img click: ", xy_x, xy_y
                            subprocess.call(
                                'adb -s ' + serial + " shell input tap " + str((xy_x1 - xy_x) / 2 + xy_x) + " " + str(
                                    (xy_y1 - xy_y) / 2 + xy_y))
                            time.sleep(2)
                            self.logger.info(str(index) + " " + serial + " Click Image:" + fn.split(".")[0] + " Pass")
                            self.textout.insert(1.0,
                                                " ." + str(index) + ". " + serial + " Click Image:" + fn.split(".")[
                                                    0] + " Pass\n")
                            picname2 = os.getcwd() + "/pic/" + reporttime + "/" + time.strftime("%m%d%H%M%S",
                                                                                                time.localtime()) + "_" + str(
                                index) + "_AfterClickImage.png"
                            imgsrc = self.minicap_ins.crop_image()
                            if imgsrc == None:
                                return
                            elif imgsrc.size[0] < 10:
                                return
                            imgsrc.thumbnail((imgsrc.size[0] * 0.4, imgsrc.size[1] * 0.4), Image.ANTIALIAS)
                            imgsrc.save(picname2)
                            # self.showandclosep_threading(picname2)
                            self.stepresult[-1][1].append(
                                {"step": index, "tcs": "Click Image:" + fn.split(".")[0], "result": "Pass",
                                 "url": picname, "url2": picname2})
                    elif "imagesimilar:" in line:
                        op = "imagesimilar"
                        x = line[line.find(":") + 1:]
                        "i1,i2 or l1,id or l1,l2"
                        im1 = x.split(',')
                        print im1
                        pkg = self.getPackage()
                        back = True
                        if im1[2] != None:
                            back = False
                        i1 = pkg + ":id/" + im1[0]
                        i2 = pkg + ":id/" + im1[1]
                        print i1, i2, back
                        ssim = self.compareImage(i1, i2, bc=back)
                        print ssim
                        if ssim > 0.7:
                            result = True
                        else:
                            result = False
                        self.logger.debug("imagesimilar:" + x + ":" + str(result))
                        # self.canvas.delete('box')
        except Exception, e:
            import traceback
            traceback.print_exc()
            subprocess.Popen(['adb', '-s', serial, 'shell', 'input', 'keyevent', '4'],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            time.sleep(1)
            picname2 = os.getcwd() + "/pic/" + reporttime + "/" + time.strftime("%m%d%H%M%S",
                                                                                time.localtime()) + "_" + str(
                index) + "_Exception.png"
            imgsrc = self.minicap_ins.crop_image()
            if imgsrc == None:
                return
            elif imgsrc.size[0] < 10:
                return
            imgsrc.thumbnail((imgsrc.size[0] * 0.4, imgsrc.size[1] * 0.4), Image.ANTIALIAS)
            imgsrc.save(picname)
            self.stepresult[-1][0][0]['TotalResult'] = False
            self.stepresult[-1][1].append(
                {"step": index, "tcs": line, "result": "Fail",
                 "url": picname})
            self.textout.insert(END, "控制出错了\n")
            self.textout.update()
        finally:
            try:
                self.canvas.delete("box")
            except Exception, e:
                pass
                # return line + ":" + str(self.result)

    def findImage(self, serial, img, tw):
        imgfound = [None, None, None, None]
        imobj = ac.imread(img)
        for i in xrange(0, tw):
            try:
                time.sleep(1)
                imgsrc = ac.imread(self.d.screenshot(os.getcwd() + "/tmp.png"))
                if imgsrc < 10:
                    continue
                # src = self.minicap_ins.crop_image()
                # src.save(os.getcwd() + "/tmp.png")
                # imgsrc = ac.imread(os.getcwd() + "/tmp.png")
                rt = ac.find_template(imgsrc, imobj)
                if rt != None:
                    # cof = float(rt['confidence'][0]) / rt['confidence'][1]
                    if rt['result'][0] > 1 and rt['result'][1] > 1:
                        if float(rt['confidence']) > 0.65:
                            if int(rt['result'][0]) < int(self.WIDTH) and rt['result'][1] < int(self.HEIGHT):
                                print "image found!", rt['result'], rt['confidence']
                                imgfound = (rt['rectangle'][0][0], rt['rectangle'][0][1], rt['rectangle'][3][0],
                                            rt['rectangle'][3][1])
                                self.textout.insert(1.0,
                                                    "     发现图片，精度:" + str("%0.2f" % (rt['confidence'])) + "，位置:" + str(
                                                        rt['result']) + "\n")
                                return imgfound

                else:
                    rts = ac.find_sift(imgsrc, imobj)
                    if len(rts) > 0:
                        cof = float(rts['confidence'][0]) / rts['confidence'][1]
                        if rts['result'][0] > 1 and rts['result'][1] > 1:
                            if cof > 0.70:
                                if int(rts['result'][0]) < int(self.WIDTH) and rts['result'][1] < int(
                                        self.HEIGHT):
                                    imgfound = (
                                        rts['rectangle'][0][0], rts['rectangle'][0][1], rts['rectangle'][3][0],
                                        rts['rectangle'][3][1])
                                    print "sift image found!", rts['result'], rts['confidence']
                                    return imgfound
            except Exception, e:
                # import traceback
                # print "e.mess:", e.message
                return imgfound
        return imgfound

    def check_source_larger_than_search(self, im_source, im_search):
        """检查图像识别的输入."""
        # 图像格式, 确保输入图像为指定的矩阵格式:
        # 图像大小, 检查截图宽、高是否大于了截屏的宽、高:
        h_search, w_search = im_search.shape[:2]
        h_source, w_source = im_source.shape[:2]
        if h_search > h_source or w_search > w_source:
            print "error"

    def find_template(self, img, threshold=0.5, rgb=False, wt=10):
        """函数功能：找到最优结果."""
        self.d = Device()
        im_search = ac.imread(img.decode('u8').encode('gbk'))
        for i in xrange(0, wt):
            try:
                # 第一步：校验图像输入
                im_source = ac.imread(self.d.screenshot(os.getcwd() + "/tmp.png"))
                self.check_source_larger_than_search(im_source, im_search)
                # 第二步：计算模板匹配的结果矩阵res
                res = self._get_template_result_matrix(im_source, im_search)
                # 第三步：依次获取匹配结果
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
                h, w = im_search.shape[:2]
                # 求取可信度:
                confidence = self._get_confidence_from_matrix(im_source, im_search, max_loc, max_val, w, h, rgb)
                # 求取识别位置: 目标中心 + 目标区域:
                middle_point, rectangle = self._get_target_rectangle(max_loc, w, h)
                best_match = self.generate_result(middle_point, rectangle, confidence)
                print ("threshold=%s, result=%s" % (threshold, best_match))
                if best_match['result'][0] > 1 and best_match['result'][1] > 1 and confidence >= threshold:
                    imgfound = (
                        best_match['rectangle'][0][0], best_match['rectangle'][0][1], best_match['rectangle'][2][0],
                        best_match['rectangle'][2][1])
                    self.textout.insert(1.0,
                                        "     发现对比图,精度:(" + str("%0.3f" % (best_match['confidence'])) + ") 位置:" + str(
                                            best_match['result']) + "\n")
                    return imgfound if confidence >= threshold else None
            except Exception, e:
                return None
        self.textout.insert(1.0, "     没有找到对比图！\n")
        return None

    # return {'confidence': 0.9968975186347961, 'result': (58, 127), 'rectangle': ((22, 97), (22, 158), (94, 158), (94, 97))}


    def generate_result(self, middle_point, pypts, confi):
        """
        Format the result: 定义图像识别结果格式
        """
        ret = dict(result=middle_point,
                   rectangle=pypts,
                   confidence=confi)
        return ret

    def _get_template_result_matrix(self, im_source, im_search):
        """求取模板匹配的结果矩阵."""
        # 灰度识别: cv2.matchTemplate( )只能处理灰度图片参数
        s_gray, i_gray = self.img_mat_rgb_2_gray(im_search), self.img_mat_rgb_2_gray(im_source)
        return cv2.matchTemplate(i_gray, s_gray, cv2.TM_CCOEFF_NORMED)

    def _get_target_rectangle(self, left_top_pos, w, h):
        """根据左上角点和宽高求出目标区域."""
        x_min, y_min = left_top_pos
        # 中心位置的坐标:
        x_middle, y_middle = int(x_min + w / 2), int(y_min + h / 2)
        # 左下(min,max)->右下(max,max)->右上(max,min)
        left_bottom_pos, right_bottom_pos = (x_min, y_min + h), (x_min + w, y_min + h)
        right_top_pos = (x_min + w, y_min)
        # 点击位置:
        middle_point = (x_middle, y_middle)
        # 识别目标区域: 点序:左上->左下->右下->右上, 左上(min,min)右下(max,max)
        rectangle = (left_top_pos, left_bottom_pos, right_bottom_pos, right_top_pos)

        return middle_point, rectangle

    def _get_confidence_from_matrix(self, im_source, im_search, max_loc, max_val, w, h, rgb):
        """根据结果矩阵求出confidence."""
        # 求取可信度:
        if rgb:
            # 如果有颜色校验,对目标区域进行BGR三通道校验:
            img_crop = im_source[max_loc[1]:max_loc[1] + h, max_loc[0]: max_loc[0] + w]
            confidence = self.cal_rgb_confidence(img_crop, im_search)
        else:
            confidence = max_val
        return confidence

    def cal_rgb_confidence(self, img_src_rgb, img_sch_rgb):
        """同大小彩图计算相似度."""
        # BGR三通道心理学权重:
        weight = (0.114, 0.587, 0.299)
        src_bgr, sch_bgr = cv2.split(img_src_rgb), cv2.split(img_sch_rgb)

        # 计算BGR三通道的confidence，存入bgr_confidence:
        bgr_confidence = [0, 0, 0]
        for i in range(3):
            res_temp = cv2.matchTemplate(src_bgr[i], sch_bgr[i], cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res_temp)
            bgr_confidence[i] = max_val

        # 加权可信度
        weighted_confidence = bgr_confidence[0] * weight[0] + bgr_confidence[1] * weight[1] + bgr_confidence[2] * \
                                                                                              weight[2]
        # 只要任何一通道的可信度低于阈值,均视为识别失败, 所以也返回每个通道的
        return weighted_confidence, bgr_confidence

    def img_mat_rgb_2_gray(self, img_mat):
        """
            turn img_mat into gray_scale, so that template match can figure the img data.
            "print(type(im_search[0][0])")  can check the pixel type.
        """
        assert isinstance(img_mat[0][0], np.ndarray), "input must be instance of np.ndarray"
        return cv2.cvtColor(img_mat, cv2.COLOR_BGR2GRAY)

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

        # apkversion = self.raw_cmd( 'shell', 'dumpsys', "package", package, "|", "grep",'versionName', '|head -n 1')
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
            self.raw_cmd('shell',
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
            while ct <= int(590) and (len(xy) > 0) and runtflat:
                ct = time.time() - timeNow
                ky = xy.keys()[random.randint(0, len(xy) - 1)]  # point "md5":"100x200",ky is key
                cxy = xy.pop(ky)  # point "md5":"100x200",cxy is value
                subprocess.call(
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
                        self.raw_cmd('shell',
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

    def killMinicap(self):
        out = \
            self.raw_cmd('wait-for-device', 'shell', 'ps', '|grep', 'minicap')
        out = out.strip().split('\n')
        print "minicap:", out
        if len(out[0]) > 11:
            idx = out[0].split()[1]
            print "minicap_kill:", idx
            # pid = out[1].split()[idx]
            # print 'minicap is running, killing', idx
            self.raw_cmd('wait-for-device', 'shell', 'kill', '-9', idx)

    def killMinitouch(self):
        out = \
            self.raw_cmd('wait-for-device', 'shell', 'ps', '|grep', 'minitouch')
        out = out.strip().split('\n')
        # print "minitouch:", out
        if len(out[0]) > 11:
            idx = out[0].split()[1]
            # print "minitouch_kill:", idx
            # pid = out[1].split()[idx]
            # print 'minicap is running, killing', idx
            self.raw_cmd('wait-for-device', 'shell', 'kill', '-9', idx)

    def imagetk(self, fn):
        try:
            img = Image.open(fn)  # 打开图片
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

    def mouse_wheel_threading(self, event):
        t = threading.Thread(target=self._mouse_wheel, args=(event,))
        t.start()
        t.join()

    def _mouse_wheel(self, event):
        print "mouseevent", event
        if event.delta > 0:
            cmds = ['adb'] + ['-s'] + [self.serial] + ['shell', 'input', 'swipe', str(self.WIDTH / 2),
                                                       str(self.HEIGHT * 0.3),
                                                       str(self.WIDTH / 2), str(self.HEIGHT * 0.7)]

            subprocess.Popen(cmds, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            # os.system("adb -s F6VK85LB7PPFO7MJ shell input swipe 240 672.0 240 192.0")
        else:
            cmds = ['adb'] + ['-s'] + [self.serial] + ['shell', 'input', 'swipe', str(self.WIDTH / 2),
                                                       str(self.HEIGHT * 0.7), str(self.WIDTH / 2),
                                                       str(self.HEIGHT * 0.2)]
            subprocess.Popen(cmds, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def _mouse_click(self, event):
        self._moved = False
        c = self.canvas
        st = datetime.datetime.now()
        self._mouse_motion_xy.append([event.x, event.y])
        self.cavas_x_y[st] = (int(c.canvasx(event.x)), int(c.canvasy(event.y)))
        cavas_x, cavas_y = (int(c.canvasx(event.x)), int(c.canvasy(event.y)))
        click_x = cavas_x
        click_y = cavas_y
        if int(self.WIDTH) > 360:
            click_x *= self.WIDTH / 360.0
        else:
            click_x *= 360.0 / self.WIDTH
        if int(self.HEIGHT) > 720:
            click_y *= self.HEIGHT / 720.0
        else:
            click_y *= 720.0 / self.HEIGHT
        self.minitouch.touch((click_x, click_y), 1)
        self._mouse_motion = "click"

    def _mouse_right_click(self, event):
        d = tkinter.filedialog.asksaveasfilename(filetypes=(('Images', '*.png;*.jpg;'),),
                                                 initialfile='screen.png')
        if not d:  # canceled
            self._mouse_motion_crop = ""
            return
        if not d.endswith('.png') and not d.endswith('.jpg'):
            d += '.png'
        if str(self.WIDTH) not in d or str(self.HEIGHT) not in d:
            d = d[:-4] + "." + str(self.WIDTH) + "x" + str(self.HEIGHT) + ".png"
        imgsrc = self.minicap_ins.crop_image()
        imgsrc.save(d)
        self.textout.insert(END, "屏幕图像保存在:" + str(d) + '\n')

    def _stroke_move(self, event):
        # print "_stroke_move", event.x, event.y
        self._mouse_motion_xy.append([event.x, event.y])
        self._mouse_motion = "move"
        if self._mouse_motion_crop != "crop":
            c = self.canvas
            cavas_x, cavas_y = (int(c.canvasx(event.x)), int(c.canvasy(event.y)))
            click_x = cavas_x
            click_y = cavas_y
            if int(self.WIDTH) > 360:
                click_x *= self.WIDTH / 360.0
            else:
                click_x *= 360.0 / self.WIDTH
            if int(self.HEIGHT) > 720:
                click_y *= self.HEIGHT / 720.0
            else:
                click_y *= 720.0 / self.HEIGHT
            self.minitouch.move_start((click_x, click_y))

    def _stroke_done(self, event):
        try:
            c = self.canvas
            self.minitouch.touch_end()
            cavas_x, cavas_y = (int(c.canvasx(event.x)), int(c.canvasy(event.y)))
            if self._mouse_motion == "click":
                click_x = cavas_x
                click_y = cavas_y
                if int(self.WIDTH) > 360:
                    click_x *= self.WIDTH / 360.0
                else:
                    click_x *= 360.0 / self.WIDTH
                if int(self.HEIGHT) > 720:
                    click_y *= self.HEIGHT / 720.0
                else:
                    click_y *= 720.0 / self.HEIGHT
                if self.study_mode_flag:
                    self.d_dump(click_x, click_y)
                    time.sleep(1)
                    if self.minitch_flag:
                        pass
                        # self.minitouch.touch((click_x, click_y))
                    else:
                        self.raw_cmd('shell', ' input', 'tap', str(click_x), str(click_y))

                self.canvas.itemconfigure('select-bounds', width=2)
                # print "---",[int(cavas_x), int(cavas_y), int(cavas_x) + 5, int(cavas_y) + 5],cavas_x,cavas_y
                # self._draw_bounds([int(cavas_x) - 5, int(cavas_y) - 5, int(cavas_x) + 5, int(cavas_y) + 5])
                self.point_cycle = self.canvas.create_oval(int(cavas_x) - 5, int(cavas_y) - 5, int(cavas_x) + 5,
                                                           int(cavas_y) + 5, fill="red")
                self.textout.insert(INSERT, "clickscreen:" + str(int(click_x)) + "x" + str(int(click_y)) + "\n")

            elif self._mouse_motion == "move":
                self._mouse_motion = ""
                cavas_x, cavas_y = (int(c.canvasx(event.x)), int(c.canvasy(event.y)))
                click_x = cavas_x
                click_y = cavas_y
                motion = self._mouse_motion_xy
                if len(self._mouse_motion_xy) >= 2:
                    x_start = self._mouse_motion_xy[0][0]
                    y_start = self._mouse_motion_xy[0][1]
                    x_end = self._mouse_motion_xy[-1][0]
                    y_end = self._mouse_motion_xy[-1][1]
                    if int(self.WIDTH) > 360:
                        x_start *= self.WIDTH / 360.0
                        x_end *= self.WIDTH / 360.0
                    else:
                        x_start *= 360.0 / self.WIDTH
                        x_end *= 360.0 / self.WIDTH
                    if int(self.HEIGHT) > 720:
                        y_start *= self.HEIGHT / 720.0
                        y_end *= self.HEIGHT / 720.0
                    else:
                        y_start *= 720.0 / self.HEIGHT
                        y_end *= 720.0 / self.HEIGHT
                    if self._mouse_motion_crop == "crop":
                        ti = c.create_rectangle(self._mouse_motion_xy[0][0], self._mouse_motion_xy[0][1],
                                                self._mouse_motion_xy[-1][0],
                                                self._mouse_motion_xy[-1][1], outline='red', tags='select-bounds',
                                                width=2)
                        # img = Image.open(os.getcwd() + '/maintmp.png')  # 打开图片
                        imgsrc = self.minicap_ins.crop_image()
                        imgsrc.save(os.getcwd() + '/tmp.png')

                        img = Image.open("tmp.png")
                        # print ('_mouse_crop position: %s', (x_start, y_start, x_end, y_end))
                        try:
                            tm = str(datetime.datetime.now().strftime("%m%d%H%M%S"))
                            im_crop = img.crop([x_start, y_start, x_end, y_end])
                            d = tkinter.filedialog.asksaveasfilename(filetypes=(('Images', '*.png;*.jpg;'),),
                                                                     initialfile='screen.png')
                            if not d:  # canceled
                                self._mouse_motion_crop = ""
                                return
                            if not d.endswith('.png') and not d.endswith('.jpg'):
                                d += '.png'
                            if str(self.WIDTH) not in d or str(self.HEIGHT) not in d:
                                d = d[:-4] + "." + str(self.WIDTH) + "x" + str(self.HEIGHT) + ".png"
                            print 'Save to', d
                            im_crop.save(d.strip())
                            if self.enable_script:
                                if tkinter.messagebox.askokcancel('提示', '对此区域操作：点击选<是>,检查选<否>'):
                                    x, y = float(x_start) + (float(x_end) - float(x_start)) / 2, float(y_start) + (
                                        float(y_end) - float(y_start)) / 2
                                    print x_start, x_end, y_start, y_end, ",", x, y
                                    self.raw_cmd('shell', ' input', 'tap', str(x), str(y))
                                    self.textout.insert(INSERT, "clickimage:" + str(d) + '\n')
                                    self.textout.insert(INSERT, 'sleep:1\n')
                                else:
                                    self.textout.insert(INSERT, "checkimage:" + str(d) + '\n')
                                    self.textout.insert(INSERT, 'sleep:1\n')
                                self.textout.update()
                            else:
                                im_crop.show()
                                self.textout.insert(END, "截图保存在:" + str(d) + '\n')
                                self.textout.update()

                            self._mouse_motion_crop = ""
                        except Exception, e:
                            # import traceback
                            # traceback.print_exc()
                            pass
                        finally:
                            c.delete(ti)
                        if self.enable_script:
                            self.textout.insert(END,
                                                "swipe:" + str(x_start) + "," + str(y_start) + "," + str(
                                                    x_end) + "," + str(y_end) + "\n")
                            self.textout.insert(END, "sleep:1 \n")
                            self.textout.update()
                            # else:
                            #     print "---------------------->"
                            #     if int(self.WIDTH) > 360:
                            #         motion[0][0] = motion[0][0] * self.WIDTH / 360.0
                            #         motion[0][1] = motion[0][1] * self.HEIGHT / 720.0
                            #     else:
                            #         motion[0][0] = motion[0][0] * 360.0 / self.WIDTH
                            #         motion[0][1] = motion[0][1] * 360.0 / self.HEIGHT
                            #     self.minitouch.operate({"type": "down", "x": motion[0][0], "y": motion[0][1]})
                            #     for i in xrange(1, len(self._mouse_motion_xy) - 1):
                            #         if int(self.WIDTH) > 360:
                            #             motion[i][0] = motion[i][0] * self.WIDTH / 360.0
                            #             motion[i][1] = motion[i][1] * self.HEIGHT / 720.0
                            #         else:
                            #             motion[i][0] = motion[i][0] * 360.0 / self.WIDTH
                            #             motion[i][1] = motion[i][1] * 360.0 / self.HEIGHT
                            #         self.minitouch.operate({"type": "move", "x": motion[i][0], "y": motion[i][1]})
                            #     if int(self.WIDTH) > 360:
                            #         motion[-1][0] = motion[-1][0] * self.WIDTH / 360.0
                            #         motion[-1][1] = motion[-1][1] * self.HEIGHT / 720.0
                            #     else:
                            #         motion[-1][0] = motion[-1][0] * 360.0 / self.WIDTH
                            #         motion[-1][1] = motion[-1][1] * 360.0 / self.HEIGHT
                            #     self.minitouch.operate({"type": "up"})
                            #     motion = []
                            #     if self.enable_script:
                            #         self.textout.insert(END,
                            #                             "swipe:" + str(x_start) + "," + str(y_start) + "," + str(
                            #                                 x_end) + "," + str(y_end) + "\n")
                            #         self.textout.insert(END, "sleep:1\n")
                            #         self.textout.update()

        except Exception, e:
            pass
            # import traceback
            # traceback.print_exc()
        finally:
            if self.point_cycle > 2:
                for i in xrange(2, self.point_cycle):
                    c.delete(i)
            self._mouse_motion_xy = []
            self.cavas_x_y = {}
            motion = []

    def _draw_bounds(self, bounds, color='red', tags='select-bounds'):
        try:
            c = self.canvas
            (x0, y0, x1, y1) = bounds
            i = c.create_oval(x0, y0, x1, y1, fill="red")
            if i > 2:
                c.delete(i - 1)
        except Exception, e:
            pass

    def crop_image_show(self):
        if not self.enable_script:
            self.textout.insert(END, "\n请用鼠标左键，在右侧屏幕画出截取区域！\n")
            self.textout.update()
        self._mouse_motion_crop = "crop"

        # tkinter.messagebox.showinfo(title="提示框", message="用鼠标在右侧屏幕上画出要截取的位置，方框内图像即可保存到本地文件maintmp_crop.png")

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

    def inputStr(self):
        r = dl.askstring('输入要点击的文字', '输入文字', initialvalue='')
        print(r)

    def control_edit(self, mode="clicktext"):

        if mode == "clicktext":
            self.textout.insert(INSERT, "clicktext:Settings\n")
        elif mode == "clickscreen":
            self.textout.insert(INSERT, "clickscreen:200x300\n")
        elif mode == "longclickscreen":
            self.textout.insert(INSERT, "longclickscreen:200x300\n")
        elif mode == "screenon":
            self.textout.insert(INSERT, "screenon:on/off \n")
        elif mode == "takeshot":
            self.textout.insert(INSERT, "takeshot:1 \n")
        elif mode == "clickimage":
            self.textout.insert(INSERT, "clickimage:maintmp.720x1440.png\n")
        elif mode == "startapp":
            self.textout.insert(INSERT, "startapp:pkg\n")
        elif mode == "checktext":
            self.textout.insert(INSERT, "checktext:Settings\n")
        elif mode == "waitfortext":
            self.textout.insert(INSERT, "waitfortext:Settings,2\n")
        elif mode == "checkimage":
            self.textout.insert(INSERT, "checkimage:maintmp_crop.png,20\n")
        elif mode == "pressback":
            self.textout.insert(INSERT, "pressback:1\n")
        elif mode == "pressrecent":
            self.textout.insert(INSERT, "pressrecent:1\n")
        elif mode == "presshome":
            self.textout.insert(INSERT, "presshome:1\n")
        elif mode == "playrecord":
            self.textout.insert(INSERT, "playrecord:recordfile.txt\n")
        elif mode == "install":
            self.textout.insert(INSERT, "install:app.apk\n")
        elif mode == "uninstall":
            self.textout.insert(INSERT, "uninstall:com.android.app\n")
        elif mode == "loop":
            self.textout.insert(INSERT, "loop:3 \n")
            self.textout.insert(INSERT, "<loopcode> \n")
            self.textout.insert(INSERT, "endloop\n")
        elif mode == "launch":
            self.textout.insert(INSERT, "launch:com.android.app\n")
        elif mode == "scrolltotext":
            self.textout.insert(INSERT, "scrolltotext:text\n")
        elif mode == "imagesimilar":
            self.textout.insert(INSERT, "imagesimilar:i1,i2 or l1,id or l1,l2\n")

        elif mode == "reboot":
            self.textout.insert(INSERT, "reboot\n")
        elif mode == "shell":
            self.textout.insert(INSERT, "shell\n")
        self.textout.update()

    def device_info_thread(self, serial):
        try:
            from uiautomator import Device
            self.d = Device(serial)
        except Exception, e:
            self.installbundle(serial)
            print "retry:", self.serial

    def control_openfile(self):
        try:
            self.enable_script = True
            self.study_mode_flag = False
            # t = threading.Thread(target=self.device_info_thread, args=(self.serial,)).start()
            self.radionButton_type_value.set("pressure")
            self.textout.unbind("<KeyPress-Return>")
            self.canvas.unbind_all("<Key-space>")
            self.canvas.unbind_all("<Key>")
            self.canvas.unbind_all("<KeyPress-Up>")
            self.canvas.unbind_all("<KeyPress-Down>")
            self.canvas.unbind_all("<KeyPress-Left>")
            self.canvas.unbind_all("<KeyPress-Right>")

            self.textout.delete("1.0", END)
            self.textout.update()
            ref = self.fileEdit.get()
            if ref == "":
                # ref = dl.askstring('文件打开', '输入要打开的文件名', initialvalue='')
                ref = tkinter.filedialog.asksaveasfilename(
                    filetypes=[("test file", "*.txt"), ("json file", "*.json"), ("all", "*.*")])
                if type(ref) == dict:
                    ref = ref[0]
                self.fileEdit.set(ref)

            with open(ref, 'r') as f:

                if ".json" in ref:
                    jf = json.load(f)
                    a = json.dumps(jf, sort_keys=True, indent=2)
                    # print a
                    self.textout.insert(END, a + "\n")
                    self.textout.update()
                else:
                    lines = f.read().split("\n")
                    for line in lines:
                        if len(line) > 1:
                            self.textout.insert(END, line + "\n")
                    self.textout.update()
        except Exception, e:
            self.textout.delete(1.0, END)
            # self.textout.insert(END, "没有需要打开的文件！\n")
            # self.textout.update()

    def control_save(self, event):
        try:
            self.enable_script = False
            content = self.textout.get("1.0", END)
            ref = self.fileEdit.get()
            print "save as:", ref
            if ref == "":
                ref = tkinter.filedialog.asksaveasfilename(
                    filetypes=[("text file", "*.txt"), ("json file", "*.json"), ("all", "*.*")])
                if len(ref) < 1:
                    return
                if ".txt" not in ref:
                    ref = ref + ".txt"
            file = io.open(ref, 'w+', encoding='utf8')
            # with open(ref, 'w+',encoding='utf8') as file:
            file.write(content + '\n')
            file.close()

            # self.textout.insert(END, "保存完成！")
            # self.textout.update()
            (path, shotname) = os.path.split(ref)
            if tkinter.messagebox.askokcancel('提示', '是否保存到 Json 用例文件？'):
                fn = tkinter.filedialog.asksaveasfilename(filetypes=[("json file", "*.json"), ("all", "*.*")])
                if type(fn) == dict:
                    fn = fn[0]
                json_dict = self.parser_test_case(fn)
                if json_dict == None or json_dict == 0:
                    json_dict = {'Testcases': [{'ID': shotname, 'URL': glob.glob(ref)[0]}]}
                    with open(fn, 'w') as jsfile:
                        json.dump(json_dict, jsfile)
                        a = json.dumps(json_dict, sort_keys=True, indent=2)
                        self.fileEdit.set("")
                        self.textout.insert(END, a + "\n")
                        self.textout.update()

                else:
                    tc = json_dict["Testcases"]
                    if tc != None:
                        json_dict["Testcases"].append({"ID": shotname, "URL": glob.glob(ref)[0]})
                    # jsfile = io.open(fn[0], 'w', encoding='utf8')
                    with open(fn, 'w') as jsfile:
                        json.dump(json_dict, jsfile)
                        a = json.dumps(json_dict, sort_keys=True, indent=2)
                        self.fileEdit.set("")
                        self.textout.insert(END, a + "\n")
                        self.textout.update()


        except UnicodeEncodeError, e:
            import traceback
            traceback.print_exc()
            tkinter.messagebox.showinfo(title="提示框",
                                        message="不能包含中文！\n")
        except Exception, e:
            import traceback
            traceback.print_exc()
            tkinter.messagebox.showinfo(title="提示框",
                                        message="出错了！\n")

    def enable_root(self):
        try:
            rooturl = r"http://osgroup.jstinno.com:8082/encrypt/key/encrypt"
            serial = [self.serial]
            if tkinter.messagebox.askokcancel('提示', 'root所有设备点<是>,<否>仅仅root当前设备:' + self.serial):
                serial = self.getAdb2()
            else:
                pass
            for i in xrange(0, len(serial)):
                self.serial = serial[i]
                data = {"keyString": self.serial}
                r = requests.post(rooturl, data=data)  # 在一些post请求中，还需要用到headers部分，此处未加，在下文中会说到
                out = "OK"
                ency = ""
                if "encryptString" in r.content:
                    ency = r.json().get("encryptString").encode()
                    out = self.raw_cmd('shell', 'setprop', 'persist.tinno.debug', str(ency))
                    self.raw_cmd('shell', 'setprop', 'persist.qiku.adb.input', '1')
                    self.raw_cmd('root')
                    self.raw_cmd('remount')
                self.textout.insert(END, "Root :" + self.serial + " -> " + str(ency) + " \n")
                self.textout.update()
        except Exception, e:
            self.textout.insert(END, "Root Fail! \n")
            self.textout.update()

    def enable_wifi_thread(self, tp, ps):
        t = threading.Thread(target=self.enable_wifi, args=(tp, ps,))
        t.start()

    def enable_wifi(self, tp, ps):
        try:
            self.inidevice()
            serial = [self.serial]
            # if tkinter.messagebox.askokcancel('提示', '连接所有设备wifi点<是>,<否>仅连接当前设备:' + self.serial):
            #     serial = self.getAdb2()
            # else:
            #     pass
            for i in xrange(0, len(serial)):
                self.serial = serial[i]
                d = Device(self.serial)
                try:
                    cmds = ['adb'] + ['-s'] + [self.serial] + ['wait-for-device', 'shell', 'svc', 'wifi', 'enable']
                    p = subprocess.Popen(cmds, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()[0]
                    time.sleep(0.5)
                    cmds = ['adb'] + ['-s'] + [self.serial] + ['wait-for-device', 'shell', 'am', 'start', '-S', '-W',
                                                               'com.android.settings/com.android.settings.Settings']
                    p = subprocess.Popen(cmds, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()[0]
                    time.sleep(2)
                    if d(textContains="WLAN").exists:
                        d(textContains="WLAN").click()
                        time.sleep(1)
                        d(text="WLAN").click()
                    elif d(textContains="Network").exists:
                        d(textContains="Network").click()
                        time.sleep(1)
                        d(text="Wi‑Fi").click()
                    time.sleep(2)
                    d(scrollable=True).scroll.to(text=tp)
                    time.sleep(1)
                    d(text=tp).click()
                    time.sleep(1)
                    if not d(textContains="FORGET").exists:
                        d(className="android.widget.EditText").set_text(ps)
                        d(resourceId="android:id/button1").click()
                        time.sleep(0.5)
                        print self.serial + " OK"
                    self.textout.insert(END, self.serial + " connect wifi OK! \n")
                    self.textout.update()
                except Exception, e:
                    # import traceback
                    # traceback.print_exc()
                    pass
                finally:
                    self.raw_cmd('shell', 'input', 'keyevent', '4')
                    time.sleep(0.1)
                    self.raw_cmd('shell', 'input', 'keyevent', '4')
                    time.sleep(0.1)
                    self.raw_cmd('shell', 'input', 'keyevent', '3')
                    time.sleep(0.1)

        except Exception, e:
            import traceback
            traceback.print_exc()
            self.textout.insert(END, self.serial + " connect wifi Fail! \n")
            self.textout.update()

    def install_app(self):
        serial = self.getAdb2()
        fn = tkinter.filedialog.askopenfilenames(filetypes=[("apk file", "*.apk"), ("all", "*.*")])
        if len(serial) > 1:
            if tkinter.messagebox.askokcancel('提示', '安装应用到所有设备<是>,<否>仅安装到当前设备:' + self.serial):
                pass
            else:
                serial = [self.serial]
        for fl in (fn):
            for i in xrange(0, len(serial)):
                self.serial = serial[i]
                self.textout.insert(END, 'Install:' + str(fl) + '\n')
                self.textout.update()
                t = threading.Thread(target=self.install_thread, args=(fl,))
                t.start()
                t.join()

    def install_thread(self, fn):
        cmds = ['adb', '-s', self.serial, 'install', '-r', fn]
        p = subprocess.Popen(cmds, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out = p.communicate()[0]
        self.textout.insert(1.0, 'install ' + fn + ':' + out + '\n')
        self.textout.update()
        return out

    def push_res(self):
        try:
            serial = [self.serial]
            if tkinter.messagebox.askokcancel('提示', 'push到所有设备sdcard点<是>,<否>仅仅push到当前设备:' + self.serial):
                serial = self.getAdb2()
            else:
                pass
            res = dl.askstring('PUSH文件到手机sdcard', '输入要PUSH的文件', initialvalue='')
            for i in xrange(0, len(serial)):
                self.serial = serial[i]
                self.raw_cmd('push', res, '/sdcard/')
                self.textout.insert(END, "PUSH文件到:" + self.serial + " OK! \n")
                self.textout.update()
        except UnicodeEncodeError, e:
            # import traceback
            # traceback.print_exc()
            tkinter.messagebox.showinfo(title="提示框",
                                        message="不能包含中文！\n")
        except Exception, e:
            import traceback
            traceback.print_exc()
            tkinter.messagebox.showinfo(title="提示框",
                                        message="出错了！\n")

    def net_flow_tool(self):
        self.emmc_start = {}
        st = datetime.datetime.now()
        getp = self.shell_cmd('cat /proc/net/dev')
        if (len(getp) > 0) and ('No such file' not in getp):
            line = getp.strip().split("\n")
            for i in line:
                if 'wlan0:' in i:
                    wlan_r = '%.2f' % (float(i.split(":")[1].strip().split()[0]) / 1024 / 1024)
                    wlan_x = '%.2f' % (float(i.split(":")[1].strip().split()[8]) / 1024 / 1024)
                    self.textout.insert(END, "wlan0 接受数据：" + str(wlan_r) + " M \n")
                    self.textout.insert(END, "wlan0 发送数据：" + str(wlan_x) + " M \n")
                    self.textout.update()
                elif 'rmnet_data0:' in i:
                    net_r = '%.2f' % (float(i.split(":")[1].strip().split()[0]) / 1024 / 1024)
                    net_x = '%.2f' % (float(i.split(":")[1].strip().split()[8]) / 1024 / 1024)
                    self.textout.insert(END, "移动数据接收：" + str(net_r) + " M \n")
                    self.textout.insert(END, "移动数据发送：" + str(net_x) + " M \n")
                    self.textout.update()

    def emmc_start_tool(self, serial):
        self.logger = MyLogger("EMMC_Log")
        self.emmc_start = {}
        st = datetime.datetime.now()
        if len(serial) > 1:
            if tkinter.messagebox.askokcancel('提示', '所有设备执行点<是>,<否>仅仅执行当前设备:' + self.serial):
                pass
            else:
                serial = [self.serial]
        for i in xrange(0, len(serial)):
            cmds = ['adb'] + ['-s'] + [serial[i]] + ['shell', 'cat', '/proc/diskstats', '|', 'grep', '-w', 'mmcblk0']
            p = subprocess.Popen(cmds, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out = p.communicate()[0]
            if "mmcblk0" in out:
                out = out.split("mmcblk0")[1].strip().split()[6]
                self.emmc_start[st] = float(out)
                self.logger.info(self.package + " EMMC " + serial[i] + " " + str(out))
                self.textout.insert(END, serial[i] +
                                    " EMMC：" + str(
                    datetime.datetime.now().strftime("%m/%d-%H:%M:%S")) + "<" + str(
                    out) + ">\n")
            cmds = ['adb'] + ['-s'] + [serial[i]] + ['shell', 'cat', '/proc/net/dev']
            p = subprocess.Popen(cmds, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out = p.communicate()[0]
            if (len(out) > 0) and ('No such file' not in out):
                line = out.strip().split("\n")
                for k in line:
                    if 'wlan0:' in k:
                        wlan_r = '%.2f' % (float(k.split(":")[1].strip().split()[0]) / 1024 / 1024)
                        wlan_x = '%.2f' % (float(k.split(":")[1].strip().split()[8]) / 1024 / 1024)
                        self.textout.insert(END, serial[i] +
                                            " WIFI_R：" + str(
                            datetime.datetime.now().strftime("%m/%d-%H:%M:%S")) + "<" + str(
                            wlan_r) + ">M \n")
                        self.textout.insert(END, serial[i] +
                                            " WIFI_T：" + str(
                            datetime.datetime.now().strftime("%m/%d-%H:%M:%S")) + "<" + str(
                            wlan_x) + ">M \n")
                        self.logger.info("WIFI_R " + serial[i] + " " + str(wlan_r) + "M")
                        self.logger.info("WIFI_T " + serial[i] + " " + str(wlan_x) + "M")
                    elif 'rmnet_data0:' in k:
                        net_r = '%.2f' % (float(k.split(":")[1].strip().split()[0]) / 1024 / 1024)
                        net_x = '%.2f' % (float(k.split(":")[1].strip().split()[8]) / 1024 / 1024)
                        self.textout.insert(END, serial[i] +
                                            ":DATA_R：" + str(
                            datetime.datetime.now().strftime("%m/%d-%H:%M:%S")) + "<" + str(net_r) + ">M \n")
                        self.textout.insert(END, serial[i] +
                                            ":DATA_T：" + str(
                            datetime.datetime.now().strftime("%m/%d-%H:%M:%S")) + "<" + str(net_x) + ">M \n")
                        self.logger.info("DATA_R " + serial[i] + " " + str(net_r) + "M")
                        self.logger.info("DATA_T " + serial[i] + " " + str(net_x) + "M")
            self.textout.update()
            # getp = self.shell_cmd('cat /proc/diskstats | grep -w mmcblk0')

    def emmc_end_tool(self):
        try:
            st = datetime.datetime.now()
            getp = self.shell_cmd('cat /proc/diskstats | grep -w mmcblk0')
            if "mmcblk0" in getp:
                getp = getp.split("mmcblk0")[1].strip().split()[6]
                self.emmc_end[st] = float(getp)
            if len(self.emmc_start) == 1 and len(self.emmc_end) == 1:
                del_time = (self.emmc_end.keys()[0] - self.emmc_start.keys()[0]).total_seconds()
                del_data = self.emmc_end.get(self.emmc_end.keys()[0]) - self.emmc_start.get(self.emmc_start.keys()[0])
                del_data_per_min = del_data * 512 / 1024 / 1024 / (del_time / 60)
                self.textout.insert(END, "EMMC 此刻数据：" + str(
                    datetime.datetime.now().strftime("%m/%d-%H:%M:%S")) + " < " + str(
                    getp) + " > \n")
                self.textout.insert(END, "EMMC 每分钟写入：" + str('%.2f' % del_data_per_min) + " M \n")
                self.textout.update()
        except Exception, e:
            pass
        finally:
            self.emmc_end = {}

    def emmc_tool(self):
        try:
            import schedule
            import time
            # schedule.every(10).minutes.do(job)
            schedule.every().hour.do(self.schedule_job)
            # schedule.every().day.at("10:30").do(job)
            # schedule.every(5).to(10).days.do(job)
            # schedule.every().monday.do(job)
            # schedule.every().wednesday.at("13:15").do(job)
            if self.job_plan:
                self.job_plan = not self.job_plan

            while self.job_plan:
                schedule.run_pending()
                time.sleep(1)
            self.textout.insert(END, "EMMC OK! \n")
            self.textout.update()
        except UnicodeEncodeError, e:
            # import traceback
            # traceback.print_exc()
            tkinter.messagebox.showinfo(title="提示框",
                                        message="不能包含中文！\n")
        except Exception, e:
            import traceback
            traceback.print_exc()
            tkinter.messagebox.showinfo(title="提示框",
                                        message="出错了！\n")

    def command_shell(self, serial):
        res = dl.askstring('执行命令', '输入如install,pull,push,ls,rm...', initialvalue='')
        if len(res) >= 2:
            if len(serial) > 1:
                if tkinter.messagebox.askokcancel('提示', '所有设备执行点<是>,<否>仅仅执行当前设备:' + self.serial):
                    pass
                else:
                    serial = [self.serial]
            for i in xrange(0, len(serial)):
                cmd = res.split()
                # out = self.raw_cmd('shell', res)
                if res.strip().split()[0] == "install":
                    cmds = ['adb'] + ['-s'] + [serial[i]] + cmd
                else:
                    cmds = ['adb'] + ['-s'] + [serial[i]] + ['shell'] + cmd
                p = subprocess.Popen(cmds, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                out = p.communicate()[0]
                self.textout.insert(1.0, '-' * 48 + '\n')
                self.textout.insert(1.0, 'adb -s ' + serial[i] + ' ' + str(cmd) + '\n')
                self.textout.insert(1.0, out + '\n')
                self.textout.insert(1.0, '-' * 48 + '\n')
                self.textout.update()

    def clear_textout(self, event):
        self.textout.delete("1.0", END)

    def adb_log(self):
        out = self.raw_cmd('shell', 'logcat', '-d')
        self.textout.insert(1.0, 'adb -s ' + self.serial + ' shell logcat -d \n')
        self.textout.insert(1.0, '-' * 52 + '\n')
        self.textout.insert(1.0, out)
        self.textout.insert(1.0, '-' * 52 + '\n')
        self.textout.update()

    # def show_hint(self,text):
    #     print "-->",text

    def adb_mode(self, event):
        content = self.textout.get(1.0, END).lower()
        cmd = content.split()
        if self.study_mode_flag:
            content = self.textout.get(1.0, END).lower()
            cmd = content.split()
        else:
            if content.strip().split()[0] == "install":
                cmds = ['adb'] + ['-s'] + [self.serial] + cmd
            else:
                cmds = ['adb'] + ['-s'] + [self.serial] + ['shell'] + cmd

            p = subprocess.Popen(cmds, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out = p.communicate()[0]
            self.textout.insert(1.0, '-' * 52 + '\n')
            self.textout.insert(1.0, 'adb -s ' + self.serial + ' ' + str(content) + '\n')
            self.textout.insert(1.0, out + '\n')
            self.textout.insert(1.0, '-' * 52 + '\n')
            self.textout.update()

    def launche_test(self):
        ln = tkinter.messagebox.askokcancel('提示', '测试后，是否需要卸载应用？')
        fn = tkinter.filedialog.askdirectory()
        if fn != "":
            lt = IULTest.testadd(serial=self.serial, filename=fn)
            self.textout.insert(END, '测试开始，请等待结束....\n')
            self.textout.update()

            self.launche_test_thread(lt, ln)
            self.textout.insert(END, '测试完成后，请打开报告launche.html\n')
            self.textout.update()
        else:
            self.textout.insert(END, '文件为空，测试结束....\n')
            self.textout.update()

    def launche_test_thread(self, tm, ln):
        t = threading.Thread(target=tm.to_go, args=(ln,))
        t.start()

    def auto_close_thread(self, tm):
        t = threading.Thread(target=self.auto_close, args=(tm,))
        t.start()

    def auto_close(self, tm):
        for i in range(tm):
            time.sleep(1)
            print i
        self.minicap_ins.killMinicap()
        sys.exit(1)

    def update_myself(self):
        try:
            url = 'http://172.16.21.56/api/tools/GFXTest'
            request = urllib2.Request(url)  # Manual encoding required
            basestr = encodestring('%s:%s' % ('tools', 'tools'))[:-1]
            request.add_header('Authorization', 'Basic %s' % basestr)
            handler = urllib2.urlopen(request)
            get_v = handler.read()
            get_version = eval(str(get_v))
            get_ftp = get_version["GFXTest"]
            gfx_version = re.sub('[^\d\.+]', '', get_ftp[-12:-4])
            self.textout.insert(END, "TTMS GFXTest Version:" + gfx_version + '\n')
            # return get_ftp,get_version
            if self.versionCompare(VERSION, gfx_version) == 2:
                if tkinter.messagebox.askokcancel('提示', 'TTMS上发现新版本:' + str(gfx_version) + '，请更新！'):
                    self.textout.insert(END, get_ftp + "\n")
                    self.textout.update()
                    self.download_thread(get_ftp, gfx_version)
        except Exception, e:
            # import traceback
            # traceback.print_exc()
            tkinter.messagebox.askokcancel('提示', 'TTMS连接不上，请查看网络状况!')
        finally:
            print "connect to ttms ok"

    def versionCompare(self, v1, v2):
        v1_check = re.match("\d+(\.\d+){0,2}", v1)
        v2_check = re.match("\d+(\.\d+){0,2}", v2)
        if v1_check is None or v2_check is None or v1_check.group() != v1 or v2_check.group() != v2:
            print "error!"
            return 0
        v1_list = v1.split(".")
        v2_list = v2.split(".")
        v1_len = len(v1_list)
        v2_len = len(v2_list)
        if v1_len > v2_len:
            for i in range(v1_len - v2_len):
                v2_list.append("0")
        elif v2_len > v1_len:
            for i in range(v2_len - v1_len):
                v1_list.append("0")
        else:
            pass
        for i in range(len(v1_list)):
            if int(v1_list[i]) > int(v2_list[i]):
                return 1
            if int(v1_list[i]) < int(v2_list[i]):
                return 2
        return 3

    def download_thread(self, url, version):
        t = threading.Thread(target=self.download_new_version, args=(url, version,))
        t.start()
        self.textout.delete(1.0, END)
        self.textout.insert(END, "Downloading.")
        while t.isAlive():
            self.textout.insert(END, ".")
            self.textout.update()
            time.sleep(1)
            print "donwloading...."
        self.textout.delete(1.0, END)
        self.textout.insert(END, "Download Finished!\n")
        self.textout.insert(END, "Save to :" +os.getcwd() + "/GFXTest_" + str(version) + ".zip \n")


    def download_new_version(self, url, version):
        from ftplib import FTP
        ftp = FTP()
        url = url.replace("ftp://172.16.21.56/", "")
        ftp.connect("172.16.21.56", 21, 30)
        ftp.login("tinnolava", "tinnolava")
        bufsize = 1024
        fp = open(os.getcwd() + "/GFXTest_" + str(version) + ".zip", 'wb')
        get = ftp.retrbinary('RETR %s' % url, fp.write, bufsize)
        print "get:", get
        ftp.set_debuglevel(0)
        fp.close()
        ftp.quit()

        # self.textout.insert(END, "gfxtest on ttms:\n")
        # self.textout.update()
        # f = urllib2.urlopen(url)
        # data = f.read()
        # with open("GFXTest_"+str(version)+".zip", "wb") as code:
        #     code.write(data)

    def getConfig(self, section, key):
        import ConfigParser
        config = ConfigParser.ConfigParser()
        path = os.path.split(os.path.realpath(__file__))[0] + '/gfxtest.conf'
        config.read(path)
        return config.get(section, key)

    def compareImage(self, i1, i2, bc=False):
        # t = threading.Thread(target=self.device_info_thread,args=(self.serial,)).start()
        print i1, i2, bc
        otcimage = videotest.OTCImage(self.d)
        b = self.d(resourceId=i1).info["bounds"]
        box = (b["left"], b["top"], b["right"] - b["left"], b["bottom"] - b["top"])
        # box=(0,198,769,870-198)
        print box
        img_0 = otcimage.cropScreenShot(self.d, box)
        b = self.d(resourceId=i2).info["bounds"]
        box = (b["left"], b["top"], b["right"] - b["left"], b["bottom"] - b["top"])
        # box = (769, 198, 769, 870 - 198)
        print box
        img_1 = otcimage.cropScreenShot(self.d, box)
        if not bc:
            img_1 = img_1.transpose(Image.FLIP_LEFT_RIGHT)
        ssim = float(otcimage.calc_similar(img_0, img_1))
        return ssim

    def get_sdk_thread(self):
        self.textout.delete(1.0, END)
        self.textout.insert(END, "获取数据中，请耐心等候！\n")
        self.logger = MyLogger("SDK_Log")
        t = threading.Thread(target=self.get_sdk).start()

    def get_sdk(self):
        allpkg = []
        out = self.raw_cmd('shell', 'pm list package')
        for k in (out.strip().split("\r")):
            pkg = k[k.find("package:") + 8:]
            allpkg.append(pkg)
            v = self.getAPKVersion(pkg)
            self.textout.insert(END, pkg + " " + v[2])
            self.logger.info(pkg + " " + v[2])
        self.textout.update()

    def cts_test_threading(self, mou):
        p_mou = mou
        t = threading.Thread(target=self.cts_test, args=(p_mou,))
        t.setDaemon(True)
        t.start()

    def cts_test(self, py_module):
        ip_module = importlib.import_module(py_module)
        cs = getattr(ip_module, "CTSTest")
        csb = cs(device=self.d, serial=self.serial)
        csb.test_DeviceOwneTest()

    def xmlParser(self, tree, x, y):
        x = x
        y = y
        root = tree.getroot()
        root_lists = []
        for child in root:
            root_list = [child.tag, child.attrib]
            root_lists.append(root_list)
            # print child.tag, child.attrib
        node = root.findall('node')
        t = self.parserNode([{'text': '', 'bounds': '', 'resource-id': '', 'class': '', 'hm': 0}], node, x, y)
        print "t:", t
        for i in xrange(0, len(t) - 2):
            if t[0]['class'] != "":
                if t[0]['hm'] > t[1]['hm']:
                    t.pop(0)
                else:
                    t.pop(1)
        return t

    def parserNode(self, nc, node, x, y):
        for i in xrange(0, len(node)):
            bounds = node[i].attrib['bounds']
            text = node[i].attrib['text']
            className = node[i].attrib['class']
            resourceId = node[i].attrib['resource-id']
            # print bounds,text,className,resourceId
            t = bounds.replace("][", ",").replace("bounds=", "").replace("\"", "")
            t1 = t.replace("[", "").replace("]", "").split(",")
            t2 = [int(t1[0]), int(t1[1]), int(t1[2]), int(t1[3])]
            # print text,t2
            # print abs(x - (t2[2] - t2[0]) / 2),abs(y - (t2[3] - t2[1]) / 2)
            if len(node[i].findall('node')) != 0:
                self.parserNode(nc, node[i], x, y)
            hmx = int(abs(x - (t2[0] + (t2[2] - t2[0]) / 2)))
            hmy = int(abs(y - (t2[1] + (t2[3] - t2[1]) / 2)))
            hmjl = hmx * hmy
            if hmx < (self.WIDTH) * 0.1 and hmy < (self.HEIGHT) * 0.1:
                if len(text) > 0:
                    nc.insert(0, {'text': '', 'bounds': '', 'resource-id': '', 'class': '', 'hm': 0})
                    nc[0]["text"] = text
                    nc[0]["bounds"] = bounds
                    nc[0]["class"] = className
                    nc[0]["resource-id"] = resourceId
                    nc[0]["hm"] = hmjl
                print "innode:", nc
        return nc

    def d_dump_threading(self, x, y):
        try:
            self.textout.delete(1.0, END)
            t = self.d.dump("test.xml")
            tree = ET.parse("test.xml")
            t = self.xmlParser(tree, x, y)
            print "dumping", t
            if type(t) == list:
                for i in t:
                    if len(i["text"]) > 0:
                        self.textout.insert(INSERT,
                                            "clicktext:" + i["text"] + "\nbounds: " + i["bounds"] + "\nresourceId: " +
                                            i[
                                                "resource-id"] + "\nclassName: " + i["class"] + "\n")

        except Exception, IndexError:
            import traceback
            traceback.print_exc()
            print "out of range"
        except Exception, e:
            self.d.dump("test.xml")
            tree = ET.parse("test.xml")
            t = self.xmlParser(tree, x, y)
            if type(t) == list:
                for i in t:
                    if len(i["text"]) > 0:
                        self.textout.insert(INSERT, "clicktext:" + i["text"] + "\nbounds: " + i[
                            "bounds"] + "\nresourceId: " + i["resource-id"] + "\nclassName: " + i[
                                                "class"] + "\n")
                        # self.textout.insert(INSERT, "clicktext:" + i["text"] + "\nbounds: " + i[
                        #    "bounds"] + "\nresourceId: " + i["resource-id"] + "\nclassName: " + i[
                        #                        "class"] + "\n")

    def d_dump(self, x, y):
        # self.get_cpuT()
        t = threading.Thread(target=self.d_dump_threading, args=(x, y,))
        t.setDaemon(True)
        t.start()

    def study_mode_threading(self):
        self.study_mode_flag = not self.study_mode_flag
        self.textout.insert(END, "UI Viewer mode: " + str(self.study_mode_flag) + "\n")
        if self.study_mode_flag:
            threading.Thread(target=self.study_mode).start()

    def study_mode(self):
        try:
            t = self.d.dump("test.xml")
            time.sleep(1)

        except Exception, e:
            t = self.d.dump("test.xml")

    def draw_step_threading(self, box):
        t = threading.Thread(target=self.draw_step, args=(box,))
        t.start()
        t.join()

    def draw_step(self, box):
        try:
            xy = box
            # print xy
            drawline = self.canvas.create_line(xy[0], xy[1], xy[2], xy[3], fill="orange", dash=(4, 4), width=2,
                                               tags="box")
            drawline1 = self.canvas.create_line(xy[0], xy[3], xy[2], xy[1], fill="orange", dash=(4, 4), width=2,
                                                tags="box")
            orange = self.canvas.create_rectangle(xy, outline='red', width=3, tags="box")
            # time.sleep(2)
            # self.canvas.delete("box")
        except Exception, e:
            import traceback
            traceback.print_exc()
            print "draw_step error"

    def cavas_step_threading(self, file):
        t = threading.Thread(target=self.cavas_step, args=(file,))
        t.start()
        t.join()

    def cavas_step(self, file):
        try:
            # img = Image.open("1.720x1440.png")  # 打开图片
            # w, h = img.size
            # if w > 120 or h > 120:
            #     img.thumbnail((120, 120))
            # else:
            #     img = img.resize((120, 120))
            # tkimage = ImageTk.PhotoImage(img)
            # if self.canvas_image is None:
            #     self.step_canvas = Canvas(self.root, bg="white", bd=0, highlightthickness=0, relief='ridge')
            #     self.step_canvas.place(x=620, y=70, width=120, height=120)
            #     self.step_canvas.config(width=w, height=h)
            #     self.canvas_image = self.canvas.create_image(0, 0, anchor=tkinter.NW, image=tkimage)
            # else:
            #     self.canvas.itemconfig(self.canvas_image, image=tkimage)
            # time.sleep(1)
            # self.canvas.update()
            # self.step_canvas.forget()
            img = Image.open(file)  # left
            img = img.resize((120, 120), Image.ANTIALIAS)
            phototitle = ImageTk.PhotoImage(img)
            self.canvas_image.configure(image=phototitle, bg='white', bd=0)
            time.sleep(1)
        except Exception, e:
            import traceback
            traceback.print_exc()
            print "step_canvas error"

    def showandclose(self, fx):
        try:
            img = Image.open(fx)
            img = img.resize((360, 720), Image.ANTIALIAS)
            img.show()
            time.sleep(2)
            os.system('taskkill /F /IM dllhost.exe')
        except Exception, e:
            print "show error!"

    def showandclosep_threading(self, file):
        t = threading.Thread(target=self.showandclose, args=(file,))
        t.start()
        t.join()


if __name__ == "__main__":
    test = GFXTest()
    test.gettk()
    # test.find_template()
    # test.cts_test("cts_8")
    # d = Device()
    # test.findImage(d)
    # dm = DeviceMixin(d)
    # dm.wait("2.480x960.png", timeout=10, threshold=0.6)
    # d=Device()
    # d.dump("test.xml")
    # tree = ET.parse("test.xml")
    # test.xmlParser(tree, 353, 1295)
    # test.pUnit_test("cts_8")
    # test.compareImage("com.android.cts.verifier:id/preview_view","com.android.cts.verifier:id/format_view",False)


    # test.travelApp("com.android.settings")
    # test.grantPermission("com.myos.camera")
    # test.platformRun2()
    # test.travel2("com.qiku.smartkey")
    # test.recordatx()
