#!/system/bin/sh

show_help() {
echo "
Usage: sh fps.sh [ -t target_FPS ] [ -w monitor_window ] [ -k KPI ] [ -f csv_path ] [ -h ]

Show: FU(s) LU(s) Date FPS Frames jank MFS(ms) OKT SS(%)

	FU(s): Uptime of the first frame.
	LU(s): Uptime of the last frame.
	Date: The date and time of LU.
	FPS: Frames Per Second.
	Frames: All frames of a loop.
	jank: When the frame latency crosses a refresh period, jank is added one.
	MFS(ms): Max Frame Spacing.
	OKT: Over KPI Times. The KPI is the used time of one frame.
	SS(%): Smoothness Score. SS=(FPS/The target FPS)*50+(KPI/MFS)*10+(1-OKPIT/Frames)*40

POSIX options | GNU long options

	-t   | --target         The target FPS of the choosed window. Default: 60
	-w   | --window         The choosed window. Default: no window.
	-k   | --KPI            The used time of a frame. Default: KPI=1000/The target FPS.
	-f   | --file           The path of the csv file. Default: output result to console.
	-h   | --help           Display this help and exit
"
}

file=""
window=""
target=60
KPI=16
while :
do
    case $1 in
        -h | --help)
            show_help
            exit 0
            ;;
        -t | --target)
            shift
			target=$1
			KPI=$((1000/$1))
			shift
            ;;
        -w | --window)
            shift
			window="$1"
			shift
            ;;
        -k | --KPI)
            shift
			KPI=$1
			shift
            ;;
        -f | --file)
            shift
			file="$1"
			shift
            ;;
        --) # End of all options
            shift
            break
            ;;
        *)  # no more options. Stop while loop
            break
            ;;	
    esac
done

if [ -f /data/local/tmp/busybox ];then
	export bb="/data/local/tmp/busybox"
else
	echo "No /data/local/tmp/busybox"
	exit
fi
if [ -f /data/local/tmp/stop ];then
	$bb rm /data/local/tmp/stop
fi

if [ -f /data/local/tmp/FPS.pid ];then
	pid=`cat /data/local/tmp/FPS.pid`
	if [ -f /proc/$pid/cmdline ];then
		if [ `$bb awk 'NR==1{print $1}' /proc/$pid/cmdline`"a" == "sha" ];then
			echo "The $pid is sh command."
			exit
		fi
	fi
fi
echo $$ >/data/local/tmp/FPS.pid

if [ $target -le 60 -a $target -gt 0 ];then
	sleep_t=1600000
else
	echo "$target is out of (0-60]"
	exit
fi
#mac=`cat /sys/class/net/*/address|$bb sed -n '1p'|$bb tr -d ':'`
model=`getprop ro.product.model|$bb sed 's/ /_/g'`
build=`getprop ro.build.fingerprint`
if [ -z $build ];then
	build=`getprop ro.build.description`
fi

if [ -z "$file" ];then
	echo ""
	echo `date +%Y/%m/%d" "%H:%M:%S`": $window"

	while true;do
		dumpsys SurfaceFlinger --latency-clear
		uptime=$((`date +%s`-`$bb awk  '{t=$1-$1%1;if($1%1>=0.5)t+=1;print t}' /proc/uptime`))
		$bb usleep $sleep_t
		dumpsys SurfaceFlinger --latency "$window"|$bb awk -v time=$uptime -v target=$target -v kpi=$KPI '{if(NR==1){r=$1/1000000;if(r<0)r=$1/1000;if(r>kpi)kpi==r;b=0;n=0}else{if(NF==3){if($2!=0&&$2!=9223372036854775807){if(b==0){b=$2;d=0;m=r;o=0}else{c=($2-b)/1000000;if(c>500){if(n>0){t=sprintf("%.3f",b/1000000000);T=strftime("%F %T",time+t);f=sprintf("%.2f",n*1000/C);m=sprintf("%.0f",m);g=f/target;if(g>1)g=1;if(m-kpi<=1)m=kpi;h=kpi/m;e=sprintf("%.2f",g*50+h*10+(1-o/n)*40);print f+0};n=0;b=$2;C=0;d=0;m=r;o=0}else{n+=1;if(c>=r){C+=c;if(c>kpi)o+=1;if(c>=m)m=c;if(($3-$1)/1000000>r)d+=1;b=$2}else{C+=r;b=sprintf("%.0f",b+r*1000000)}}};if(n==0)s=sprintf("%.3f",$2/1000000000)}}}}END{if(n>0){t=sprintf("%.3f",b/1000000000);T=strftime("%F %T",time+t);f=sprintf("%.2f",n*1000/C);m=sprintf("%.0f",m);g=f/target;if(g>1)g=1;if(m-kpi<=1)m=kpi;h=kpi/m;e=sprintf("%.2f",g*50+h*10+(1-o/n)*40);print f+0}}'
		if [ -f /data/local/tmp/stop ];then
			break
		fi
	done
else
	start_time="`date +%Y/%m/%d" "%H:%M:%S`"
	echo "PID:$$\nWindow:$window\nT-FPS:$target\nKPI:$KPI\nStart time:$start_time\nmodel:$model\nmac:$mac\nbuild:$build"
#	echo "FU(s),LU(s),Date:$window,FPS:$target,Frames,jank,MFS(ms),OKT:$KPI,SS(%)" >$file
	while true;do
		dumpsys SurfaceFlinger --latency-clear
		uptime=$((`date +%s`-`$bb awk  '{t=$1-$1%1;if($1%1>=0.5)t+=1;print t}' /proc/uptime`))
		$bb usleep $sleep_t
		dumpsys SurfaceFlinger --latency "$window"|$bb awk -v time=$uptime -v target=$target -v kpi=$KPI '{if(NR==1){r=$1/1000000;if(r<0)r=$1/1000;if(r>kpi)kpi==r;b=0;n=0}else{if(NF==3){if($2!=0&&$2!=9223372036854775807){if(b==0){b=$2;d=0;m=r;o=0}else{c=($2-b)/1000000;if(c>500){if(n>0){t=sprintf("%.3f",b/1000000000);T=strftime("%F %T",time+t);f=sprintf("%.2f",n*1000/C);m=sprintf("%.0f",m);g=f/target;if(g>1)g=1;if(m-kpi<=1)m=kpi;h=kpi/m;e=sprintf("%.2f",g*50+h*10+(1-o/n)*40);print f+0};n=0;b=$2;C=0;d=0;m=r;o=0}else{n+=1;if(c>=r){C+=c;if(c>kpi)o+=1;if(c>=m)m=c;if(($3-$1)/1000000>r)d+=1;b=$2}else{C+=r;b=sprintf("%.0f",b+r*1000000)}}};if(n==0)s=sprintf("%.3f",$2/1000000000)}}}}END{if(n>0){t=sprintf("%.3f",b/1000000000);T=strftime("%F %T",time+t);f=sprintf("%.2f",n*1000/C);m=sprintf("%.0f",m);g=f/target;if(g>1)g=1;if(m-kpi<=1)m=kpi;h=kpi/m;e=sprintf("%.2f",g*50+h*10+(1-o/n)*40);print f+0}}' >>$file
		if [ -f /data/local/tmp/stop ];then
			echo "Stop Time:`date +%Y/%m/%d" "%H:%M:%S`"
			break
		fi
	done
fi
