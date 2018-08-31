#!/usr/bin/env python
# -*- coding: utf-8 -*-
import psutil
gfx=0
for i in psutil.pids():
    try:
        p=psutil.Process(i)
        print p.name().lower().split(".")[0][0:6]
        if p.name().lower().split(".")[0][0:7] =="gfxtest":
            print p.name()
            gfx= gfx+1
    except Exception,e:
        continue
print gfx
