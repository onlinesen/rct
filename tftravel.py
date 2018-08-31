#!/usr/bin/end python
# -*- coding: utf-8 -*-
import collections
import hashlib
import time
import xml.dom.minidom

from uiautomator import Device


class Directions:
    UP = 'Up'
    DOWN = 'Down'
    LEFT = 'Left'
    RIGHT = 'Right'


class Actions:
    CLICK = 'click'
    SWIPE = 'swipe'
    BACK = 'back'


BLACK_CLASS = (
    "android.widget.FrameLayout", "android.view.View", "android.view.ViewGroup", "android.widget.LinearLayout",
    "android.support.v7.app.ActionBar$Tab", "android.support.v7.widget.LinearLayoutCompat",
    "android.support.v7.widget.RecyclerView", "android.widget.RelativeLayout", "android.widget.ListView")

BLACK_RESOURCE = ("com.android.deskclock:id/fab", "com.android.deskclock:id/stopwatch_time_text")
BLACK_TEXT = ["Screen saver"]


class TfTravel(object):
    def __init__(self):
        self.d = Device()
        self.Q = collections.OrderedDict()
        self.stats = 0  # 0 本界面，1新界面
        self.package = "com.android.deskclock"
        self.mainpagemd5, self.mainpagenode = self.parserxml()
        # logging.basicConfig(level=logging.DEBUG,
        #                     format='%(asctime)s %(levelname)s: %(message)s')

    def performaction(self, act=Actions.CLICK, para=(100, 200)):
        if act == Actions.CLICK:
            self.d.click(para[0], para[1])
            self.d.wait.idle()
            time.sleep(1)
        elif act == Actions.BACK:
            self.d.press.back()
        return self.parserxml()

    def returnmd5(self, str):
        md5str = str
        m1 = hashlib.md5()
        m1.update(md5str.encode("utf-8"))
        token = m1.hexdigest()
        return token

    def getxml(self):
        t = self.d.dump(filename=None, compressed=False)
        # with open("test.xml") as f:
        #     t = f.read()
        DOMTree = xml.dom.minidom.parseString(t.encode("utf-8"))
        Data = DOMTree.documentElement
        nodes = Data.getElementsByTagName("node")
        return nodes

        # 解析xml，返回页面所有节点[((y,x),nodemd5)]/页面MD5

    def parserxml(self):
        pagestr = ""
        nodes_list = []  # collections.OrderedDict()
        nodes = self.getxml()
        for i in nodes:
            bound = i.getAttribute('bounds').strip()
            classname = i.getAttribute('class').strip()
            text = i.getAttribute('text').strip()
            resourceid = i.getAttribute('resource-id').strip()
            package = i.getAttribute('package').strip()
            if classname not in BLACK_CLASS and resourceid not in BLACK_RESOURCE and text not in BLACK_TEXT and package == self.package:  # 过滤节点，获取可操作bounds
                _ = bound.replace("][", ",").replace("bounds=", "").replace("\"", "")
                __ = _.replace("[", "").replace("]", "").split(",")
                # box = (int(__[0]), int(__[1]), int(__[2]), int(__[3]))
                x = int(__[0]) + (int(__[2]) - int(__[0])) / 2
                y = int(__[1]) + (int(__[3]) - int(__[1])) / 2
                box = (y, x)
                if box not in nodes_list:
                    # nodes_list[box] = {}
                    nodes_list.append(box)
                    pagestr = pagestr + classname + resourceid + bound + text
                nodes_list.sort(reverse=False)
        # sorted_nodes_list = sorted(nodes_list.items(), key=operator.itemgetter(0))  # 按照Y-X 排序
        pagemd5 = self.returnmd5(pagestr)
        return pagemd5, nodes_list

    def compareblack(self):
        if len(self.cycle) == 3 and self.cycle[0] == self.cycle[1] and self.cycle[1] == self.cycle[2]:
            self.cycle = []
            return True
        return False

    def startstravel(self):

        # #pagecontainer={mainpagemd5:mainpagenode}
        for i in self.mainpagenode:
            clicknode = i
            self.mainpagenode.remove(i)
            click = clicknode[0]
            print "move clicknode:", clicknode
            self.performaction(act=Actions.CLICK, para=(click[1], click[0]))
            time.sleep(1)
            subpagemd5, subpagenode = self.parserxml()
            if subpagemd5 != self.mainpagemd5:
                self.mainpagenode.append(clicknode)

                # if self.compareblack():
                #     mainpagenode.remove(clicknode)
                self.startstravel()
                #     subpagenode, subpagemd5 = self.parserxml()
                #     click = i.get(subpagemd5)
                #     self.performaction(act=Actions.CLICK, para=(click[1], click[0]))
                #     subpagenode, subpagemd5 = self.parserxml()
                #     if subpagemd5 not in pagecontainer:
                #         pagecontainer[subpagemd5] = subpagenode
                #     else:
                #         pagecontainer.get()

    def looptravel(self):
        popclick = ()
        container = {self.mainpagemd5: self.mainpagenode}
        lastpage = self.mainpagenode
        lastpagemd5 = self.mainpagemd5
        while True:
            nowpagemd5, nowpage = self.parserxml()
            print nowpagemd5, lastpagemd5
            if nowpagemd5 != lastpagemd5:  # 进入不同的页面
                if nowpagemd5 not in container:
                    container[nowpagemd5] = nowpage
                    self.stats = 1
            else:
                self.stats = 0
            if self.stats == 0:  # 如果在本界面：
                pass
            elif self.stats == 1:  # 如果新界面：
                # 如果返回了一个已经存在的界面，说明是返回的，要去掉这个返回键
                if nowpagemd5 not in container:
                    lastpage.insert(0, popclick)
                    if popclick not in container.get(lastpagemd5):
                        container.get(lastpagemd5).insert(0, popclick)

            if len(container.get(nowpagemd5)) > 0:
                popclick = container.get(nowpagemd5).pop(0)
                self.performaction(act=Actions.CLICK, para=(popclick[1], popclick[0]))
                time.sleep(1)
                lastpage, lastpagemd5 = nowpage, nowpagemd5
                lastpopclick = popclick

    def performclick(self, x, y):
        self.performaction(act=Actions.CLICK, para=(x, y))
        return self.parserxml()

    def looptravel1(self):
        container = self.mainpagenode
        oldmd5 = self.mainpagemd5
        oldpage = self.mainpagenode
        tree = container
        for i in xrange(len(self.mainpagenode)):
            click = container[i]
            nowpagemd5, nowpage = self.performaction(act=Actions.CLICK, para=(click[1], click[0]))
            if nowpagemd5 != oldmd5:
                container[i] = [i] + nowpage
                for j in xrange(len(nowpage)):
                    self.looptravel2(nowpagemd5, nowpage[j])

    def looptravel2(self, md5, node):
        nowpagemd5, nowpage = self.performaction(act=Actions.CLICK, para=(node[1], node[0]))
        if nowpagemd5 != md5:#new world
            return nowpagemd5, nowpage
        else:
            return None


if __name__ == "__main__":
    mi = TfTravel()
    mi.looptravel1()
    # mi.startstravel()
    # mi.parserxml("test.xml")
