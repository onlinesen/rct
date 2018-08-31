#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys,datetime

reload(sys)
sys.setdefaultencoding('utf-8')
REPORTHEAD = """<?xml version="1.0" encoding="UTF-8"?>
        <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
        <html xmlns="http://www.w3.org/1999/xhtml">
        <head>
            <title>GFX Tool Report</title>
            <meta name="generator" content="HTMLTestRunner 0.8.2"/>
            <meta http-equiv="Content-Type" content="text/html; charset=UTF-8"/>

        <style type="text/css" media="screen">
        body        { font-family: verdana, arial, helvetica, sans-serif; font-size: 90%; }
        table       { font-size: 100%;  table-layout:fixed}
        pre         { }

        /* -- heading ---------------------------------------------------------------------- */
        h1 {
        	font-size: 18pt;
        	color: gray;
        }
        .heading {
            margin-top: 0ex;
            margin-bottom: 1ex;
        }

        .heading .attribute {
            margin-top: 1ex;
            margin-bottom: 0;
        }

        .heading .description {
            margin-top: 4ex;
            margin-bottom: 6ex;
        }

        /* -- css div popup ------------------------------------------------------------------------ */
        a.popup_link {
        }

        a.popup_link:hover {
            color: red;
        }

        .popup_window {
            display: none;
            position: relative;
            left: 0px;
            top: 0px;
            /*border: solid #627173 1px; */
            font-family: "Lucida Console", "Courier New", Courier, monospace;
            text-align: center;
            font-size: 14pt;
        }

        }
        /* -- report ------------------------------------------------------------------------ */
        #show_detail_line {
            margin-top: 3ex;
            margin-bottom: 1ex;
        }
        #result_table {
            width: 90%;
            border-collapse: collapse;
            border: 1px solid #777;
        }
        #header_row {
            font-weight: bold;
            color: white;
            background-color: #777;
        }
        #result_table td {
            border: 1px solid #777;
            padding: 2px;
        }
        #total_row  { font-weight: bold; }
        .passClass  { background-color: #33CC99; }
        .failClass  { background-color: #FF9933; }
        .errorClass { background-color: #c00; }
        .passCase   { color: #339933;font-weight: bold;  }
        .failCase   { color: #FF9933; font-weight: bold; }
        .errorCase  { color: #c00; font-weight: bold; }
        .hiddenRow  { display: none; }
        .testcase   { margin-left: 2em; word-wrap:break-word;
    word-break:break-all; }


        /* -- ending ---------------------------------------------------------------------- */
        #ending {
        }

        </style>

        </head>
        <body>
        <script language="javascript" type="text/javascript"><!--
        output_list = Array();

        /* level - 0:Summary; 1:Failed; 2:All */
        function showCase(level) {
            trs = document.getElementsByTagName("tr");
            for (var i = 0; i < trs.length; i++) {
                tr = trs[i];
                id = tr.id;
                if (id.substr(0,2) == 'ft') {
                    if (level < 1) {
                        tr.className = 'hiddenRow';
                    }
                    else {
                        tr.className = '';
                    }
                }
                if (id.substr(0,2) == 'pt') {
                    if (level > 1) {
                        tr.className = '';
                    }
                    else {
                        tr.className = 'hiddenRow';
                    }
                }
            }
        }


        function showClassDetail(cid, count) {
            var id_list = Array(count);
            var toHide = 1;
            for (var i = 0; i < count; i++) {
                tid0 = 't' + cid.substr(1) + '.' + (i+1);
                tid = 'f' + tid0;
                tr = document.getElementById(tid);
                if (!tr) {
                    tid = 'p' + tid0;
                    tr = document.getElementById(tid);
                }
                id_list[i] = tid;
                if (tr.className) {
                    toHide = 0;
                }
            }
            for (var i = 0; i < count; i++) {
                tid = id_list[i];
                if (toHide) {
                    document.getElementById('div_'+tid).style.display = 'none'
                    document.getElementById(tid).className = 'hiddenRow';
                }
                else {
                    document.getElementById(tid).className = '';
                }
            }
        }


        function showTestDetail(div_id){
            var details_div = document.getElementById(div_id)
            var displayState = details_div.style.display
            // alert(displayState)
            if (displayState != 'block' ) {
                displayState = 'block'
                details_div.style.display = 'block'
            }
            else {
                details_div.style.display = 'none'
            }
        }


        function html_escape(s) {
            s = s.replace(/&/g,'&amp;');
            s = s.replace(/</g,'&lt;');
            s = s.replace(/>/g,'&gt;');
            return s;
        }
        </script>

        <div class='heading'>
        <h1>Tinno Test Report</h1>
        <p class='attribute'><strong>NJ Automation Team</strong></p>
        <p >TestDate</p>
        </div>
        <p id='show_detail_line'>Show
        <a href='javascript:showCase(0)'>Summary</a>
        <a href='javascript:showCase(1)'>Failed</a>
        <a href='javascript:showCase(2)'>All</a>
        </p>
        <table id='result_table'>
        <colgroup>
        <col align='left' width="30%"/>
        <col align='right' />
        <col align='right' />
        <col align='right' />
        <col align='right' />
        <col align='right' />
        </colgroup>
        <tr id='header_row'>
            <td>Test Group/Test case</td>
            <td>Count</td>
            <td>Pass</td>
            <td>Fail</td>
            <td>Error</td>
            <td>View</td>
        </tr>
        <tr """

REPORTAIL = """</table><div id='ending'>&nbsp;</div></body></html>"""


class ReportGen():
    def __init__(self, info):
        self.info = info
        self.pass_count = 0
        self.fail_count = 0
        self.total_count = 0
        self.repeattimes = self.info[0][0][0]["Times"]
        self.report_name = self.info[0][0][0]["ResportName"]
        self.case_pass = True

    def getresult(self):
        for i in xrange(0, len(self.info)):
            # for j in xrange(0, len(self.info[i][1])):
                if self.info[i][0][0]['TotalResult']:
                    self.pass_count = self.pass_count + 1
                else:
                    self.fail_count = self.fail_count + 1
                    self.case_pass = False
        self.total_count = len(self.info)
        return self.pass_count, self.fail_count

    def report_text_hide(self):
        PASS = """<tr id='ptx' class='none'>
            <td class='passCase'><div class='testcase'>UITest</div></td>
            <td colspan='5' align='center'>
            <!--css div popup start-->
            <a class="popup_link" onfocus='this.blur();' href="javascript:showTestDetail('div_ptx')" >
                Pass</a>
            <div id='div_ptx' class="popup_window">
                <div style='text-align: right; color:red;cursor:pointer'>
                <a onfocus='this.blur();' onclick="document.getElementById('div_ptx').style.display = 'none' " >
                   [x]</a>
                </div>
                <pre>"""

        FAIL = """ <tr id='ftx' class='none'>
                            <td class='failCase'><div class='testcase'>UITest</div></td>
                            <td colspan='5' align='left'>
                            <!--css div popup start-->
                            <a class="popup_link" onfocus='this.blur();' href="javascript:showTestDetail('div_ftx')" >
                                Fail</a>
                            <div id='div_ftx' class="popup_window">
                                <div style='text-align: right; color:red;cursor:pointer'>
                                <a onfocus='this.blur();' onclick="document.getElementById('div_ftx').style.display = 'none' " >
                                   [x]</a>
                                </div>
                                <pre>"""

        url_content = ""
        cycle_content = ""
        med_content = ""
        total_content = str(self.total_count) + """</td><td>""" + str(self.pass_count) + """</td>
                    <td>""" + str(self.fail_count) + """</td><td>0</td><td></td></tr>"""
        for i in xrange(0, len(self.info)):  # 循环次，添加用例标题
            step_pass = 0
            step_fail = 0
            case_content = ""
            self.testcase_name = self.info[i][0][0]["TestFileName"]
            for j in xrange(0, len(self.info[i][1])):
                result = self.info[i][1][j]["result"]
                step = self.info[i][1][j]["tcs"]
                url = self.info[i][1][j]["url"]
                url_content = "<img src='" + url + "' width='50%' height='50%'/> \n"
                # print j,step
                if result == "Pass":
                    step_pass = step_pass + 1
                    case_content = case_content + PASS.replace("UITest",
                                                               step) + url_content + """</pre></div></td></tr>"""
                    case_content = case_content.replace("ptx", "pt" + str(i) + "." + str(j))
                else:
                    step_fail = step_fail + 1
                    case_content = case_content + FAIL.replace("UITest",
                                                               step) + url_content + """</pre></div></td></tr>"""
                    case_content = case_content.replace("ftx", "ft" + str(i) + "." + str(j))
                cycle_content = """<tr class='""" + ("fail" if step_fail > 0 else "pass") + """Class'>
                                                                                <td>""" + self.testcase_name + """</td>
                                                                                <td>""" + str(step_pass + step_fail) + """</td>
                                                                                <td>""" + str(step_pass) + """</td>
                                                                                <td>""" + str(step_fail) + """</td><td>0</td>
                                                                                <td><a href="javascript:showClassDetail('c1',1)">Detail</a></td></tr>"""

                cycle_content = cycle_content + case_content
            med_content = med_content + cycle_content

        content = REPORTHEAD + """class='""" + (
        "fail" if self.fail_count > 0 else "pass") + """Class'id='total_row'><td>TotalTestCases</td><td>""" + total_content + med_content
        with open(os.getcwd() + "/Report/" + self.report_name + "/Report.html", 'w') as reportname:
            reportname.write(content)

    def report_text(self):
        PASS = """<tr id='ptx' class='none'>
            <td class='passCase'><div class='testcase'>UITest</div></td>
            <td colspan='5' align='left'>"""

        FAIL = """ <tr id='ftx' class='none'>
                            <td class='failCase'><div class='testcase'>UITest</div></td>
                            <td colspan='5' align='left'>"""

        url_content = ""
        cycle_content = ""
        med_content = ""
        total_content = str(self.total_count) + """</td><td>""" + str(self.pass_count) + """</td>
                    <td>""" + str(self.fail_count) + """</td><td>0</td><td></td></tr>"""
        for i in xrange(0, len(self.info)):  # 循环次，添加用例标题
            step_pass = 0
            step_fail = 0
            case_content = ""
            self.testcase_name = self.info[i][0][0]["TestFileName"]
            for j in xrange(0, len(self.info[i][1])):
                result = self.info[i][1][j]["result"]
                step = self.info[i][1][j]["tcs"]
                url = self.info[i][1][j]["url"]
                url2 = self.info[i][1][j].get('url2')
                url_content = "<img class='lazy'   data-echo='" + url + "' width='49%' border='1'/> \n"
                if url2 != None:
                    url_content = url_content + "<img class='lazy'   data-echo='" + url2 + "' width='49%' border='1'/> \n"
                # print j,step
                if result == "Pass":
                    step_pass = step_pass + 1

                    case_content = case_content + PASS.replace("UITest", step) + url_content + """</td></tr>"""
                    case_content = case_content.replace("ptx", "pt" + str(i) + "." + str(j))
                else:
                    step_fail = step_fail + 1
                    case_content = case_content + FAIL.replace("UITest", step) + url_content + """</td></tr>"""
                    case_content = case_content.replace("ftx", "ft" + str(i) + "." + str(j))
                cycle_content = """<tr class='""" + ("fail" if step_fail > 0 else "pass") + """Class'>
                                                                                <td>""" + self.testcase_name + """</td>
                                                                                <td>""" + str(step_pass + step_fail) + """</td>
                                                                                <td>""" + str(step_pass) + """</td>
                                                                                <td>""" + str(step_fail) + """</td><td>0</td>
                                                                                <td><a href="javascript:showClassDetail('c1',1)">Detail</a></td></tr>"""

                cycle_content = cycle_content + case_content
            med_content = med_content + cycle_content
        t = REPORTHEAD.replace("TestDate", "Report Date:"+str(datetime.datetime.now().strftime("%Y/%m/%d %H:%M")))
        content = t + """class='""" + (
            "fail" if self.fail_count > 0 else "pass") + """Class'id='total_row'><td>Total TestCases/Steps</td><td>""" + total_content + med_content + """<script src="../../lib/bundle/lazyload.js"></script>
<script>Echo.init({offset: 0,throttle: 0});</script>""" + REPORTAIL
        with open(os.getcwd() + "/Report/" + self.report_name + "/Report.html", 'w') as reportname:
            reportname.write(content)


if __name__ == "__main__":
    # info1 = [{"ResportName": "123", "TotalResult": True, 'TestFileName': "test1.txt", 'Times': 2},
    #          [{"step": 1, "tcs": "clicktext","result": "Fail", "url": r"E:\work\GFXTest\pic\0510131514\0510131529_1_CheckText_Pass.png"},
    #           {"step": 2, "tcs": "checktext","result": "Pass", "url": r"E:\work\GFXTest\pic\0510131514\0510131554_4_CheckImage_Fail.png"}
    #          ],
    #          [{"step": 1, "tcs": "clicktext", "result": "Fail",
    #            "url": r"E:\work\GFXTest\pic\0510131514\0510131529_1_CheckText_Pass.png"},
    #           {"step": 2, "tcs": "checktext", "result": "Fail",
    #            "url": r"E:\work\GFXTest\pic\0510131514\0510131554_4_CheckImage_Fail.png"}
    #           ]
    #          ]
    # info1 = [{"ResportName": "0514085917", "TotalResult": True, 'TestFileName': "test1.txt", 'Times': 2},
    #          [{"step": 1, "tcs": "clicktext", "result": "Pass",
    #            "url": r"E:\work\GFXTest\pic\0514085917\0514085926_0_ClickText_Pass.png"},
    #           {"step": 2, "tcs": "checktext", "result": "Pass",
    #            "url": r"E:\work\GFXTest\pic\0514085917\0514085926_0_ClickText_Pass.png"}
    #           ],
    #          [{"step": 1, "tcs": "clicktext", "result": "Fail",
    #            "url": r"E:\work\GFXTest\pic\0514085917\0514085926_0_ClickText_Pass.png"},
    #           {"step": 2, "tcs": "checktext", "result": "Fail",
    #            "url": r"E:\work\GFXTest\pic\0514085917\0514085926_0_ClickText_Pass.png"}
    #           ],
    #          [{"step": 1, "tcs": "clicktext", "result": "Fail",
    #            "url": r"E:\work\GFXTest\pic\0514085917\0514085926_0_ClickText_Pass.png"},
    #           {"step": 2, "tcs": "checktext", "result": "Pass",
    #            "url": r"E:\work\GFXTest\pic\0514085917\0514085926_0_ClickText_Pass.png"}
    #           ],
    #          [{"step": 1, "tcs": "clicktext", "result": "Pass",
    #            "url": r"E:\work\GFXTest\pic\0514085917\0514085926_0_ClickText_Pass.png"},
    #           {"step": 2, "tcs": "checktext", "result": "Fail",
    #            "url": r"E:\work\GFXTest\pic\0514085917\0514085926_0_ClickText_Pass.png"}
    #           ]
    #          ]
    info1 = [
        [{'TotalResult': True, 'Times': 1, 'ResportName': '0514085917', 'TestFileName': 'test1.txt'},
         [
             {'url': 'E:\\work\\GFXTest/pic/0514085917/0514085926_0_ClickText_Pass.png', 'step': 0,
              'tcs': 'Click Text:Google', 'result': 'Pass'},
             {'url': 'E:\\work\\GFXTest/pic/0514085917/0514085931_1_ClickImage_Pass.png', 'step': 1,
              'tcs': 'Click Image:1',
              'result': 'Pass'},
             {'url': 'E:\\work\\GFXTest/pic/0514085917/0514085938_4_CheckImage_Pass.png', 'step': 4,
              'tcs': 'Check Image:2',
              'result': 'Pass'}
         ]],
        [{'TotalResult': True, 'Times': 1, 'ResportName': '0514085917', 'TestFileName': 'test5.txt'},
         [
             {'url': 'E:\\work\\GFXTest/pic/0514085917/0514085926_0_ClickText_Pass.png', 'step': 0,
              'tcs': 'Click Text:Google', 'result': 'Pass'},
             {'url': 'E:\\work\\GFXTest/pic/0514085917/0514085931_1_ClickImage_Pass.png', 'step': 1,
              'tcs': 'Click Image:1',
              'result': 'Pass'},
             {'url': 'E:\\work\\GFXTest/pic/0514085917/0514085938_4_CheckImage_Pass.png', 'step': 4,
              'tcs': 'Check Image:2',
              'result': 'Pass'}
         ]]

    ]

    info2 = [[[{'TotalResult': True, 'Times': 1, 'ResportName': '0515074038',
                'TestFileName': 'E:\\work\\GFXTest\\test1.txt'}], [
                  {'url': 'E:\\work\\GFXTest/pic/0515074038/0515074056_0_ClickText_Pass.png', 'step': 0,
                   'tcs': 'Click Text:Google', 'result': 'Pass'},
                  {'url': 'E:\\work\\GFXTest/pic/0515074038/0515074101_1_ClickImage_Pass.png', 'step': 1,
                   'tcs': 'Click Image:1', 'result': 'Pass'},
                  {'url': 'E:\\work\\GFXTest/pic/0515074038/0515074110_3_CheckImage_Pass.png', 'step': 3,
                   'tcs': 'Check Image:2', 'result': 'Pass'}]]]
    info3 = [
        [[{'TotalResult': False, 'Times': 1, 'ResportName': '0523092618', 'TestFileName': '\xe5\x89\xaf\xe6\x9c\xac'}],
         [{'url': 'E:\\work\\GFXTest/pic/0523092618/0523092652_0_ClickText_Exception.png', 'step': 0,
           'url2': u'E:\\work\\GFXTest/pic/0523092618/0523092618_0_BeforClickText_ZAKER\u65b0\u95fb.png',
           'tcs': 'Click Text:ZAKER\xe6\x96\xb0\xe9\x97\xbb', 'result': 'Fail'},
          {'url': 'E:\\work\\GFXTest/pic/0523092618/0523092657_2_CheckText_Pass.png', 'step': 2,
           'tcs': ' Check Text:\xe6\x88\x91\xe7\x9a\x84', 'result': 'Pass'},
          {'url': 'E:\\work\\GFXTest/pic/0523092618/0523092658_3_CheckImage_Pass.png', 'step': 3,
           'tcs': 'Check Image:\xe6\x88\x911', 'result': 'Pass'},
          {'url': 'E:\\work\\GFXTest/pic/0523092618/0523092710_5_CheckText_Fail.png', 'step': 5,
           'tcs': ' Check Text:City', 'result': 'Fail'}]]]
    info4 = [[[{'TotalResult': False, 'Times': 3, 'ResportName': '0523101545', 'TestFileName': 'test1'}], [
        {'url': u'E:\\work\\GFXTest/pic/0523101545/0523101546_0_BeforClickText_ZAKER\u65b0\u95fb.png', 'step': 0,
         'url2': 'E:\\work\\GFXTest/pic/0523101545/0523101551_0_ClickText_Pass.png',
         'tcs': 'Click Text:ZAKER\xe6\x96\xb0\xe9\x97\xbb', 'result': 'Pass'},
        {'url': 'E:\\work\\GFXTest/pic/0523101545/0523101553_2_ClickImage_Pass.png', 'step': 2,
         'url2': 'E:\\work\\GFXTest/pic/0523101545/0523101558_2_AfterClickImage.png', 'tcs': u'Click Image:w1',
         'result': 'Pass'}, {'url': 'E:\\work\\GFXTest/pic/0523101545/0523101609_4_CheckText_Fail.png', 'step': 4,
                             'tcs': ' Check Text:City', 'result': 'Fail'}]],
             [[{'TotalResult': False, 'Times': 3, 'ResportName': '0523101545', 'TestFileName': 'test1'}], [
                 {'url': u'E:\\work\\GFXTest/pic/0523101545/0523101612_0_BeforClickText_ZAKER\u65b0\u95fb.png',
                  'step': 0, 'url2': 'E:\\work\\GFXTest/pic/0523101545/0523101617_0_ClickText_Pass.png',
                  'tcs': 'Click Text:ZAKER\xe6\x96\xb0\xe9\x97\xbb', 'result': 'Pass'},
                 {'url': 'E:\\work\\GFXTest/pic/0523101545/0523101620_2_ClickImage_Pass.png', 'step': 2,
                  'url2': 'E:\\work\\GFXTest/pic/0523101545/0523101624_2_AfterClickImage.png', 'tcs': u'Click Image:w1',
                  'result': 'Pass'},
                 {'url': 'E:\\work\\GFXTest/pic/0523101545/0523101636_4_CheckText_Fail.png', 'step': 4,
                  'tcs': ' Check Text:City', 'result': 'Fail'}]],
             [[{'TotalResult': False, 'Times': 3, 'ResportName': '0523101545', 'TestFileName': 'test1'}], [
                 {'url': u'E:\\work\\GFXTest/pic/0523101545/0523101638_0_BeforClickText_ZAKER\u65b0\u95fb.png',
                  'step': 0, 'url2': 'E:\\work\\GFXTest/pic/0523101545/0523101643_0_ClickText_Pass.png',
                  'tcs': 'Click Text:ZAKER\xe6\x96\xb0\xe9\x97\xbb', 'result': 'Pass'},
                 {'url': 'E:\\work\\GFXTest/pic/0523101545/0523101645_2_ClickImage_Pass.png', 'step': 2,
                  'url2': 'E:\\work\\GFXTest/pic/0523101545/0523101649_2_AfterClickImage.png', 'tcs': u'Click Image:w1',
                  'result': 'Pass'},
                 {'url': 'E:\\work\\GFXTest/pic/0523101545/0523101702_4_CheckText_Fail.png', 'step': 4,
                  'tcs': ' Check Text:City', 'result': 'Fail'}]]]

    rp = ReportGen(info4)
    rp.getresult()
    rp.report_text()
