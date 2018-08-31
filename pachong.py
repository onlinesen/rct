#!/usr/bin/env python
# -*- coding: utf-8 -*-
import urllib2, urllib
import cookielib

rooturl=r"http://osgroup.jstinno.com:8082/encrypt/key/encrypt"
url = r'http://ttms.tinno.com/auth/login?next=%2F'
url1 = r'http://ttms.tinno.com/tools/test-tools-version/24/'

import requests
session = requests.Session()
session.headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'
}
session.get(url)
r = session.get('http://ttms.tinno.com/tools/test-tools-version/24/')

login_data = {
    'username': 'lin.shen',
    'password': 'lin.shen',
    'bg_color': 'true'
}
session.post(url, data=login_data)
res = session.get(url1)


filename = 'cookie.txt'
#声明一个MozillaCookieJar对象实例来保存cookie，之后写入文件
cookie = cookielib.MozillaCookieJar(filename)
opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie))
postdata = urllib.urlencode({
			  'username': 'lin.shen',
    'password': 'lin.shen',
    'bg_color': 'true'
		})
#登录教务系统的URL
loginUrl =url
#模拟登录，并把cookie保存到变量
result = opener.open(loginUrl,postdata)
#保存cookie到cookie.txt中
cookie.save(ignore_discard=True, ignore_expires=True)
#利用cookie请求访问另一个网址，此网址是成绩查询网址
gradeUrl = url1
#请求访问成绩查询网址
result = opener.open(gradeUrl)
#print result.read()

import requests
import json

data={"keyString":"45GUAIW44LTOEE7H"}
r=requests.post(rooturl,data=data)         #在一些post请求中，还需要用到headers部分，此处未加，在下文中会说到
c= r.json().get("encryptString")
print type(c.encode())
print (r.json().get("encryptString")),"encryptString" in (r.content),r.content