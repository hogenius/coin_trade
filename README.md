# coin_trade

1.Ubuntu Setting
apt update : sudo apt update
pip3 install : sudo apt install python3-pip
local time(KST) set : sudo ln -sf /usr/share/zoneinfo/Asia/Seoul /etc/localtime

2.pip install
pip3 install pyupbit
pip3 install pyyaml

3. start
nohup python3 -u auto_trade.py > output.log &
