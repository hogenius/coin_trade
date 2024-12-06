#!/bin/sh

APP_NAME=trade
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")  # 스크립트의 절대 경로를 계산
APP_PID_FILE=/tmp/$APP_NAME.pid    # PID 파일 절대 경로
APP_PY_FILE=$SCRIPT_DIR/$APP_NAME.py      # Python 파일 절대 경로

case "$1" in

        start)
                if test -s "$APP_PID_FILE"
                then
                        echo "Already $APP_PID_FILE Running !"
                else
                        echo -n "Starting $APP_NAME Agent :"
                        echo "$APP_PY_FILE"
                        echo
      #nohup python3 -u "$APP_NAME".py >> "$APP_NAME".log &
          nohup python3 -u "$APP_PY_FILE" > /dev/null 2>&1 &
                        echo $! > "$APP_PID_FILE"
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
                        rm -f "$APP_PID_FILE"
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
