# coin_trade

### Ubuntu Setting
- apt update : sudo apt update
- pip3 install : sudo apt install python3-pip
- local time(KST) set : sudo ln -sf /usr/share/zoneinfo/Asia/Seoul /etc/localtime

### pip install
- pip3 install pyupbit
- pip3 install pyyaml
- pip3 install backtesting
- pip3 install python-telegram-bot
- pip3 install asyncio
- pip3 install schedule
- pip install bokeh==2.4.3
    https://github.com/kernc/backtesting.py/issues/803

### start
- nohup python3 -u auto_trade.py > output.log &
