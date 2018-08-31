#!/usr/bin/python
# -*- coding: utf-8 -*-

from PIL import Image
import os,subprocess
import time
import datetime
from uiautomator import Device
class OTCImage():
    def __init__(self,serial):
        self.serial = serial
        self.d = Device(self.serial)
        self.gResult = True

    def __make_regalur_image(self, img, size=(256, 256)):
        return img.resize(size).convert('RGB')

    def __split_image(self, img, part_size=(64, 64)):
        w, h = img.size
        pw, ph = part_size

        assert w % pw == h % ph == 0

        return [img.crop((i, j, i + pw, j + ph)).copy() \
                for i in xrange(0, w, pw) \
                for j in xrange(0, h, ph)]

    def __hist_similar(self, lh, rh):
        assert len(lh) == len(rh)
        return sum(1 - (0 if l == r else float(abs(l - r)) / max(l, r)) for l, r in zip(lh, rh)) / len(lh)

    def __calc_similar(self, li, ri):
        #    return self.__hist_similar(li.histogram(), ri.histogram())
        return sum(self.__hist_similar(l.histogram(), r.histogram()) for l, r in
                   zip(self.__split_image(li), self.__split_image(ri))) / 16.0

    # git ssim between picA and picB
    def calc_similar_by_path(self, lf, rf, median=4):
        li, ri = self.__make_regalur_image(Image.open(lf)), self.__make_regalur_image(Image.open(rf))
        return ("%." + str(median) + "f") % self.__calc_similar(li, ri)

    # git ssim between picA and picB
    def calc_similar_by_path_box(self, lf, rf, box, median=4):
        im1 = Image.open(lf).crop(box)
        im2 = Image.open(rf).crop(box)
        li, ri = self.__make_regalur_image(im1), self.__make_regalur_image(im2)
        return ("%." + str(median) + "f") % self.__calc_similar(li, ri)

    # git ssim between picA and picB
    def calc_similar(self, im1, im2, median=4):
        if im1 is None or im2 is None:
            return 0
        li, ri = self.__make_regalur_image(im1), self.__make_regalur_image(im2)
        return ("%." + str(median) + "f") % self.__calc_similar(li, ri)

    # git ssim DATA between picA and picB
    def make_doc_data(self, lf, rf):
        li, ri = self.__make_regalur_image(Image.open(lf)), self.__make_regalur_image(Image.open(rf))
        li.save(lf + '_regalur.png')
        ri.save(rf + '_regalur.png')
        fd = open('stat.csv', 'w')
        fd.write('\n'.join(l + ',' + r for l, r in zip(map(str, li.histogram()), map(str, ri.histogram()))))
        #    print >>fd, '\n'
        #    fd.write(','.join(map(str, ri.histogram())))
        fd.close()
        import ImageDraw
        li = li.convert('RGB')
        draw = ImageDraw.Draw(li)
        for i in xrange(0, 256, 64):
            draw.line((0, i, 256, i), fill='#ff0000')
            draw.line((i, 0, i, 256), fill='#ff0000')
        li.save(lf + '_lines.png')
    def raw_cmd(self, *args):
        try:
            cmds = ['adb'] + ['-s'] + [self.serial] + list(args)
            p = subprocess.Popen(cmds, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            c = p.communicate()[0]
            return c
        except Exception, e:
            pass

    def screenshot(self, filename="savescreen.png"):
        self.d.screenshot("savescreen.png")
        # out = self.raw_cmd('shell', 'wm', 'size')
        # out = out.split()[-1].split("x")
        # params = '{x}x{y}@{x1}x{y1}/{r}'.format(x=out[0], y=out[1], x1=out[0], y1=out[1], r=0)
        # self.raw_cmd('shell', 'LD_LIBRARY_PATH=/data/local/tmp', '/data/local/tmp/minicap', '-P %s' % params,
        #                  '-S -s > /sdcard/savescreen.png')
        # self.raw_cmd('pull', '/sdcard/savescreen.png')
        return filename
    #         g_common_obj.take_screenshot("adb shell /system/bin/screencap -p sdcard/screenshot.png")
    #         execCmdNoLog("adb pull sdcard/screenshot.png " + filename)
    #         execCmdNoLog("adb shell rm -rf sdcard/screenshot.png")

    def saveImage(self, device, fileName="savescreen.png"):
        #print "saveImage"
        path = self.screenshot(fileName)
        #print "screenshot,path is [%s]" % path
        return path

    def getWidgetImage(self, device, widget, imageName='widgetImage.png', save=False):
        #         imageName = Constant.LogPath + "/" + Constant.caseName + "/"+ str(time.time())+"_" + imageName
        imageName = str(time.time()) + "_" + imageName
        path = self.saveImage(device)
        img = Image.open(path)
        box = widget.bounds
        box = (box.get('left'), box.get('top'), box.get('right'), box.get('bottom'))
        img = img.crop(box)
        if save:
            img.save(imageName)
        os.system("rm -rf " + path)
        return img

    def getPicByCoor(self, device, x, y, w, h, imageName="savescreen.png", save=False):
        path = self.saveImage(device)
        img = Image.open("savescreen.png")
        box = (x, y, x + w, y + h)
        img = img.crop(box)
        if save:
            path = img.save(imageName)
            #print "screenshot, path is [%s]" % path
        return img

    def cropScreenShot(self, device, box, imageName="savescreen.png", save=False):
        if box is not None:
            return self.getPicByCoor(device, box[0], box[1], box[2], box[3], imageName, save)

    def openBoxImage(self, path):
        if path is not None:
            return Image.open(path)

    def analysisImageToString(self, img):
        result = ""
        try:
            imgs = img.split()
            if len(imgs) == 4:
                img = Image.merge("RGB", (imgs[0], imgs[1], imgs[2]))
            result = image_to_string(img)
        except:
            print "analysisImageToString failed"
        return result

    def getTmpDir(self):
        path = "/tmp"
        if not os.access(path, os.R_OK | os.W_OK):
            path = "~/tmp"
            if not os.path.exists(path):
                os.mkdir(path)
        path = os.path.join(path, "logs")
        if not os.path.exists(path):
            os.mkdir(path)
        return path

    def sim(self,setTime,box):
        try:
            otcImage = OTCImage()
            a = OTCImage()
            img_0 = otcImage.cropScreenShot(self.d, box, save=True)
            ct = 0
            timeNow = time.time()
            while ct <= int(setTime):
                time.sleep(2)
                img_1 = otcImage.cropScreenShot(self.d, box, save=True)
                ssim = float(otcImage.calc_similar(img_0, img_1))
                img_0 = img_1
                print datetime.datetime.now().strftime('%H:%M:%S') + "...Playing...." + str(ssim) + " time: "+str(int(ct))
                if ssim > 0.999:#ssim <= 0.99, "video playback has been False"
                    print "test Fail"
                    self.gResult = False
                    return self.gResult
                ct = time.time() - timeNow
        except Exception,e:
            self.gResult = False
        finally:
            return self.gResult

        # return a.calc_similar_by_path('1.png', '2.png')


if __name__ == "__main__":
   a=OTCImage()
   a.sim()