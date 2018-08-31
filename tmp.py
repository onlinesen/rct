t= [{'text': 'Audio1 Frequency Unprocessed Test', 'class': 'android.widget.TextView', 'hm':18820, 'bounds': '[30,792][1050,936]', 'resource-id': 'android:id/text1'},{'text': 'Audio Frequency Unprocessed Test', 'class': 'android.widget.TextView', 'hm': 8820, 'bounds': '[30,792][1050,936]', 'resource-id': 'android:id/text1'}, {'text': 'Audio Frequency Speaker Test', 'class': 'android.widget.TextView', 'hm': 0, 'bounds': '[30,645][1050,789]', 'resource-id': 'android:id/text1'}, {'text': 'Audio Frequency Microphone Test', 'class': 'android.widget.TextView', 'hm': 8820, 'bounds': '[30,498][1050,642]', 'resource-id': 'android:id/text1'}, {'text': '', 'class': '', 'hm': 0, 'bounds': '', 'resource-id': ''}]
print len(t)
for i in xrange(0, len(t) - 2):
    print i
    if  t[0]['class'] != "":
        if t[0]['hm'] > t[1]['hm']:
            print "0", t[0]
            t.pop(0)
        else:
            print "1", t[1]
            t.pop(1)
print t