#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os

import aircv as ac
import cv2
import numpy as np

# print circle_center_pos
def draw_circle(img, pos, circle_radius, color, line_width):
    cv2.circle(img, pos, circle_radius, color, line_width)
    cv2.imshow('objDetect', imsrc)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


def findImage():
    imgfound = [None, None, None, None]
    # imsrc = ac.imread(self.d.screenshot(os.getcwd() + "/tmp.png"))
    # src = self.minicap_ins.crop_image()
    # src.save(os.getcwd() + "/tmp.png")
    imgsrc = ac.imread("tmp.png")
    imobj = ac.imread('w1.720x1512_480x960.png')
    rt = ac.find_template(imgsrc, imobj)
    print "rt:", rt
    rts = ac.find_sift(imgsrc, imobj)
    print "snift:", rts

def check_source_larger_than_search(im_source, im_search):
    """检查图像识别的输入."""
    # 图像格式, 确保输入图像为指定的矩阵格式:
    # 图像大小, 检查截图宽、高是否大于了截屏的宽、高:
    h_search, w_search = im_search.shape[:2]
    h_source, w_source = im_source.shape[:2]
    if h_search > h_source or w_search > w_source:
       print "error"

def find_template(im_source, im_search, threshold=0.8, rgb=False):
    """函数功能：找到最优结果."""
    # 第一步：校验图像输入
    check_source_larger_than_search(im_source, im_search)
    # 第二步：计算模板匹配的结果矩阵res
    res = _get_template_result_matrix(im_source, im_search)
    # 第三步：依次获取匹配结果
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
    h, w = im_search.shape[:2]
    # 求取可信度:
    confidence = _get_confidence_from_matrix(im_source, im_search, max_loc, max_val, w, h, rgb)
    # 求取识别位置: 目标中心 + 目标区域:
    middle_point, rectangle = _get_target_rectangle(max_loc, w, h)
    best_match = generate_result(middle_point, rectangle, confidence)
    print #old=%s, result=%s" % (threshold, best_match))
    print best_match,type(best_match)
    return best_match if confidence >= threshold else None

def generate_result(middle_point, pypts, confi):
    """
    Format the result: 定义图像识别结果格式
    """
    ret = dict(result=middle_point,
               rectangle=pypts,
               confidence=confi)
    return ret
def _get_template_result_matrix(im_source, im_search):
    """求取模板匹配的结果矩阵."""
    # 灰度识别: cv2.matchTemplate( )只能处理灰度图片参数
    s_gray, i_gray = img_mat_rgb_2_gray(im_search), img_mat_rgb_2_gray(im_source)
    return cv2.matchTemplate(i_gray, s_gray, cv2.TM_CCOEFF_NORMED)

def _get_target_rectangle(left_top_pos, w, h):
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
def _get_confidence_from_matrix(im_source, im_search, max_loc, max_val, w, h, rgb):
    """根据结果矩阵求出confidence."""
    # 求取可信度:
    if rgb:
        # 如果有颜色校验,对目标区域进行BGR三通道校验:
        img_crop = im_source[max_loc[1]:max_loc[1] + h, max_loc[0]: max_loc[0] + w]
        confidence = cal_rgb_confidence(img_crop, im_search)
    else:
        confidence = max_val
    return confidence



def cal_rgb_confidence(img_src_rgb, img_sch_rgb):
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
    weighted_confidence = bgr_confidence[0] * weight[0] + bgr_confidence[1] * weight[1] + bgr_confidence[2] * weight[2]
    # 只要任何一通道的可信度低于阈值,均视为识别失败, 所以也返回每个通道的
    return weighted_confidence, bgr_confidence

def img_mat_rgb_2_gray(img_mat):
    """
        turn img_mat into gray_scale, so that template match can figure the img data.
        "print(type(im_search[0][0])")  can check the pixel type.
    """
    assert isinstance(img_mat[0][0], np.ndarray), "input must be instance of np.ndarray"
    return cv2.cvtColor(img_mat, cv2.COLOR_BGR2GRAY)

if __name__ == "__main__":
    #findImage()
    f = "我1.720x1512_480x960.png"
    a = ac.imread("tmp.png")
    b = ac.imread(f.decode('u8').encode('gbk'))
    find_template( a,b)

    #
    # imsrc = ac.imread('tmp.png')
    # imobj = ac.imread('2.720x1440_480x960.png')
    # pos = ac.find_all_template(imsrc, imobj)
    # print pos

    # circle_center_pos = pos['result']
    # circle_radius = 50
    # color = (0, 255, 0)
    # line_width = 10
    #
    # # draw circle
    # draw_circle(imsrc, circle_center_pos, circle_radius, color, line_width)
