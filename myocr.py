#!/usr/bin/env python
# -*- coding: utf-8 -*-
from aip import AipOcr
import os,re
import json
import sys
from aip import AipFace
import cv2
import subprocess
# 定义常量
APP_ID = '10804442'
API_KEY = 'Gppu03U3abbEBuHFiZQGxfGn'
SECRET_KEY = 'm7Ow24UXtGrF7PUlbKTukBgaZDCE88OI'
aipOcr = AipOcr(APP_ID, API_KEY, SECRET_KEY)
client = AipFace(APP_ID, API_KEY, SECRET_KEY)
class MYOCRTest():

    @staticmethod
    def repara():
        with open(os.getcwd() + "/tmp.png", 'rb') as fp:
            options = {
                'detect_direction': 'true',
                'language_type': 'CHN_ENG',
            }
            result = aipOcr.general(fp.read(), options)
        # rrresult = json.dumps(result).decode("unicode-escape")
        return result.get("words_result")

    @staticmethod
    def repface():
        out = subprocess.Popen(
            ['adb', 'shell', 'LD_LIBRARY_PATH=/data/local/tmp', '/data/local/tmp/minicap', '-i', ],
            stdout=subprocess.PIPE).communicate()[0]
        m = re.search('"width": (\d+).*"height": (\d+).*"rotation": (\d+)', out, re.S)
        w, h, r = map(int, m.groups())
        w, h = min(w, h), max(w, h)
        params = '{x}x{y}@{x1}x{y1}/{r}'.format(x=w, y=h, x1=w / 2, y1=h / 2, r=0)
        cmd = 'shell LD_LIBRARY_PATH=/data/local/tmp /data/local/tmp/minicap -P %s' % params + ' -S -Q 80  -s > /sdcard/facetmp.png'
        flag =True
        cv2.destroyAllWindows()
        while flag:
            try:
                res = "没有目标"
                # p = subprocess.Popen(['adb', [cmd]], stdout=None)
                p = subprocess.Popen(['adb', [cmd]], stdout=None)
                os.popen('adb pull /sdcard/facetmp.png ./facetmp.png')
                with open(os.getcwd() + "/facetmp.png", 'rb') as fp:
                    """ 如果有可选参数 """
                    options = {}
                    options["max_face_num"] = 1
                    options["face_fields"] = "age"
                    result = client.detect(fp.read(),options)
                rrresult = result.get("result")
                # print rrresult
                xy = rrresult[0].get("location")
                top = int(xy.get("top"))
                width = int(xy.get("width"))
                height = int(xy.get("height"))
                left = int(xy.get("left"))
                print U"发现目标，方位：[" + str(left) + "," + str(top) + "," + str(left+width) + "," + str(top+height) + "]"
                imgpath = os.getcwd() + "/facetmp.png"
                imgpath1 = os.getcwd() + "/facetmp_1.png"
                img = cv2.imread(imgpath)
                if int(top)>0 and int(height)>0:
                    flag = False
                    res = "发现目标：" + str(xy)

                cv2.rectangle(img, (left-10, top-10), (left+width, top+height), (0, 255, 0), 3)
                cv2.imshow("Image", img)
                k = cv2.waitKey(5) & 0xFF
                if k == 27:
                    break
            except Exception,e:
                continue
        #cv2.destroyAllWindows()
        return res


    @staticmethod
    def repic():
        from aip import AipImageCensor
        APP_ID = '10805647'
        API_KEY = '4BORuFSWdXtODzh8gjFVUzKB'
        SECRET_KEY = 'uZG60psAKFxRYZuqtQdTbree4ilaaPbB'
        client = AipImageCensor(APP_ID, API_KEY, SECRET_KEY)
        with open(os.getcwd() + "/tmp.png", 'rb') as fp:
            options = {
                'detect_direction': 'true',
                'language_type': 'CHN_ENG',
            }
            result = client.imageCensorComb(
                fp.read(), [
        'clarity',
        'antiporn',
    ]

            )
        rrresult = json.dumps(result).decode("unicode-escape")
        print rrresult

        #cv2.rectangle(im, (int(sx1), int(sy1)), (int(sx2), int(sy2)), (0, 255, 0), 3)
        # rrresult = json.dumps(result).decode("unicode-escape")
        #return result.get("words_result")


if __name__=="__main__":
    MYOCRTest.repface()