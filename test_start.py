import asyncio
import pyupbit
from torch import bmm, normal
from check_hmm import CheckHMM
from config import ConfigInfo
from test import test_class
from auto_trade_check import CoinTrade
from msg_telegram import Messaging
from check_ticker import CheckTicker
from pomegranate import *
is_test = True

if __name__ == '__main__':
    
    #upbit = pyupbit.Upbit(ConfigInfo.Instance().access, ConfigInfo.Instance().secret)

    df = pyupbit.get_ohlcv("KRW-BTC", "minutes3", 999)
    print(df)


    # 변동률 계산
    df["price_change"] = df["close"].pct_change() * 100  # 변동률 계산 (퍼센트)

    # 1. 관찰 데이터 준비 (변동률과 거래량)
    observations = df[["price_change", "volume"]].dropna().values  # NaN 제거 후 numpy 배열로 변환
    print(observations)

    # 2. 숨겨진 상태 초기화
    # 강세 (Bull Market)
    bull = normal(0.03, 0.01)  # 평균 3% 상승, 표준편차 1%
    # 약세 (Bear Market)
    bear = normal(-0.02, 0.01) # 평균 2% 하락, 표준편차 1%
    # 횡보 (Sideways Market)
    sideways = normal(0.0, 0.005) # 평균 0%, 표준편차 0.5%

    # 3. HMM 모델 생성
    model = bmm(name="Crypto Market")

    # 상태 추가
    model.add_states(bull, bear, sideways)

    # 초기 전이 확률 설정 (학습 전에는 랜덤 초기값 사용)
    model.add_transition(model.start, bull, 0.33)
    model.add_transition(model.start, bear, 0.33)
    model.add_transition(model.start, sideways, 0.34)
    model.add_transition(bull, bull, 0.5)
    model.add_transition(bull, bear, 0.3)
    model.add_transition(bull, sideways, 0.2)
    model.add_transition(bear, bear, 0.6)
    model.add_transition(bear, bull, 0.2)
    model.add_transition(bear, sideways, 0.2)
    model.add_transition(sideways, sideways, 0.7)
    model.add_transition(sideways, bull, 0.15)
    model.add_transition(sideways, bear, 0.15)

    # 4. 모델 학습 (Baum-Welch 알고리즘 실행)
    model.bake()  # 초기 상태 준비
    model.fit(observations, algorithm="baum-welch", max_iterations=100)

    # 5. 학습된 전이 확률 확인
    print("\nTransition Probabilities:")
    for i, state in enumerate(model.states):
        for j, next_state in enumerate(model.states):
            prob = model.dense_transition_matrix()[i, j]
            if prob > 0:  # 출력이 많은 것을 방지
                print(f"{state.name} -> {next_state.name}: {prob:.2f}")

    # 6. 관찰 데이터로 숨겨진 상태 예측
    hidden_states = model.predict(observations)
    print("\nPredicted Hidden States:", hidden_states)
    
    #loop.create_task(CheckTicker("CHECKER", is_test).InitRoutine())
    
    #Messaging.Instance().InitHandler()
    

    

    