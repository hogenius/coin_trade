import pyupbit
import datetime
import time
import asyncio
from auto_trade_check import CoinTrade
from config import ConfigInfo
from simple_common.simpledata import SimpleData

async def main():
    # 업비트 객체 생성
    upbit = pyupbit.Upbit(ConfigInfo.Instance().access_key, ConfigInfo.Instance().secret_key)
    
    # 코인 트레이드 객체 생성 (테스트 모드로 설정)
    coin_trade = CoinTrade("trade_hmm", upbit, True)
    
    # 이벤트 루프 시작
    await coin_trade.InitRoutine()

if __name__ == "__main__":
    # ConfigInfo 초기화 (HMM 설정 파일 사용)
    ConfigInfo.Instance().config_path = "config_hmm.yaml"
    ConfigInfo.Instance().ReloadAll()
    
    # 메인 함수 실행
    asyncio.run(main()) 