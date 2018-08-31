#!/system/bin/sh

am instrument -w -r -e debug false -e class com.tinno.autotravel.AppsTraveler#testLan com.tinno.test.appstraveler.test/android.support.test.runner.AndroidJUnitRunner & 2>&1

