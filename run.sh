#!/bin/bash

# 스크립트 이름

SCRIPT_NAME="run.sh"

# 프로그램 실행 함수

function start_program() {
  echo "프로그램 시작..."
  nohup python3 -u "$1".py > "$1".log &
  echo "프로그램 PID: $!"
}

# 프로그램 종료 함수

function stop_program() {
  echo "프로그램 종료..."
  pid=$(ps aux | grep "$1" | awk '{print $2}')
  if [ -n "$pid" ]; then
    echo "프로그램 종료 완료. $pid "
    kill -9 $pid
  else
    echo "프로그램 실행 중이 아닙니다."
  fi
}

# 매개변수 처리

if [ "$2" == "start" ]; then
  start_program "$1"
elif [ "$2" == "stop" ]; then
  stop_program "$1"
else
  echo "사용법: $SCRIPT_NAME 실행_파일_명 start|stop"
fi
