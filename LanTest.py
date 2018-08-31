# /usr/bin/env python
# coding=utf8

import httplib
import md5
import urllib
import random
import urllib2
import json
import  re
import os
import sys
import urllib2
import urllib
import HTMLParser
reload(sys)
sys.setdefaultencoding('utf-8')


class LanTest():

    def __init__(self):
        self.appKey = '1edda0c16770f46e'
        self.secretKey = 'GJM4E3eOlRCOLU97xozAdDNkr7MT70Hc'
        httpClient = None
        self.fromLang = 'ja'
        self.toLang = 'zh-CHS'

    def translate_yd(self,text = "good",from_language = "en",to_language = "zh-CHS"):
        try:
            self.myurl = '/api'
            self.salt = random.randint(1, 65536)
            self.fromLang = from_language
            self.toLang = to_language
            self.m1 = md5.new()
            self.sign = self.appKey + text + str(self.salt) + self.secretKey
            self.m1.update(self.sign)
            self.sign = self.m1.hexdigest()
            self.myurl = self.myurl + '?appKey=' + self.appKey + '&q=' + urllib.quote(text) + '&from=' + self.fromLang + '&to=' + self.toLang + '&salt=' + str(
                self.salt) + '&sign=' + self.sign
            httpClient = httplib.HTTPConnection('openapi.youdao.com')
            httpClient.request('GET', self.myurl)
            # response是HTTPResponse对象
            response = httpClient.getresponse()
            data = json.loads(response.read())
            return data
        except Exception, e:
            print e
        finally:
            if httpClient:
                httpClient.close()

    def unescape(self,text):
        parser = HTMLParser.HTMLParser()
        return (parser.unescape(text))

    def translate_google(self,text, from_language="auto",to_language="auto", ):
        agent = {'User-Agent':
                     "Mozilla/4.0 (\
                     compatible;\
                     MSIE 6.0;\
                     Windows NT 5.1;\
                     SV1;\
                     .NET CLR 1.1.4322;\
                     .NET CLR 2.0.50727;\
                     .NET CLR 3.0.04506.30\
                     )"}
        try:
            base_link = "http://translate.google.com/m?hl=%s&sl=%s&q=%s"
            text = urllib.quote_plus(text)
            link = base_link % (to_language, from_language, text)
            request = urllib2.Request(link, headers=agent)
            raw_data = urllib2.urlopen(request).read()
            data = raw_data.decode("utf-8")
            expr = r'class="t0">(.*?)<'
            re_result = re.findall(expr, data)
            if (len(re_result) == 0):
                result = ""
            else:
                result = self.unescape(re_result[0])
            return (result)
        except Exception,e:
            return ("")

if __name__ == "__main__":# fromlan = "zh-CHS",tolan = "en",从中文翻译到英文
    language1 = {'ar':"يأكل وجبة",'zh-CHS':"吃午饭", 'ja':"昼飯を食べる", 'en':"lunch", 'ko':"점심을 먹다.", 'fr':"déjeuner", 'ru':"пообедать", 'pt':"Vamos almoçar.", 'es':"almorzar", 'vi':"Ăn trưa"}
    language2 = ['zh-CHS', 'ja', 'en', 'ko', 'fr', 'ru', 'pt', 'es', 'vi']
    testlan = LanTest()
    m = sys.argv
    if len(m)==2:
        mode = m[1]
        if mode == 'y':  #有道翻译
            print u"有道翻译中...."
            for i in language1:
                for j in language1:
                    get_result  =  testlan.translate_yd(text = language1.get(i),from_language = i,to_language =j)
                    get_result_google = testlan.translate_google(text=language1.get(i), from_language=i, to_language=j)
                    if get_result_google != None:
                        print  "Google[" + str(i) + "] <" + language1.get(i).encode('utf-8') + "> to ["+str(j)+"] <" + (get_result_google).encode('utf-8') + ">"

                    if get_result.get('translation') != None:
                        print  "youdao[" + str(i) + "] <" + language1.get(i).encode('utf-8') + "> to ["+str(j)+"] <" + (get_result.get('translation')[0]).encode('utf-8') + ">"
                    if get_result.get('basic') != None:
                        for k in get_result.get('basic').get('explains'):
                            print "youdao:" + k
        else:#  谷歌翻译
            print u"谷歌翻译中...."
            #print testlan.translate_google("lunch",from_language="auto", to_language="zh-CHS" )
            for i in language1:
                for j in language1:
                    get_result  =  testlan.translate_google(text = language1.get(i),from_language = i,to_language =j)
                    if get_result != None:
                        print  "[" + str(i) + "] <" + language1.get(i).encode('utf-8') + "> to ["+str(j)+"] <" + (get_result).encode('utf-8') + ">"

