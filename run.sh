#!/bin/sh

APP_NAME=trade
APP_PID_FILE=$APP_NAME.pid

case "$1" in

	start)
		if test -s "$APP_PID"
		then
			echo "Already $APP_PID_FILE Running !" 
		else
			echo -n "Starting $APP_NAME Agent :"
			echo
      nohup python3 -u "APP_NAME".py > "APP_NAME".log &
			echo $! > $APP_PID_FILE
			echo
		fi
		;;
	
	stop)
		if test -s "$APP_PID_FILE"
		then
			APP_PID=`cat $APP_PID_FILE`
			echo "Killing $APP_NAME Agent : "
			echo
			kill -9 $APP_PID
			rm -f $APP_PID_FILE
		else
			echo "No pid file found !" 
		fi
		echo
	;;

	restart)
		$0 stop
		$0 start
	;;
	*)
		echo "Usage: $0 {start|stop|restart}"
		exit 1
esac

exit 0
