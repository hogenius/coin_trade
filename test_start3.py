import pyupbit
from hmmlearn import hmm
import numpy as np
from simple_common.simpledata import SimpleData
from config import ConfigInfo
import datetime

def classify_states(means):
    """ 각 상태(State)를 변동률과 거래량을 기준으로 분류 """
    sorted_states = sorted(enumerate(means), key=lambda x: (x[1][0], x[1][1]))  # 변동률 기준 정렬

    stable_state = sorted_states[0][0]  # 변동률이 가장 낮은 상태 (안정적인 시장)
    normal_state = sorted_states[1][0]  # 중간 변동성을 가진 상태
    volatile_state = sorted_states[2][0]  # 변동성이 가장 큰 상태 (급등/급락 시장)

    return stable_state, normal_state, volatile_state

if __name__ == '__main__':
    
    # 데이터 가져오기
    coin_name = "KRW-BTC"
    define_days=365 #10일치

    simple_data = SimpleData(ConfigInfo.Instance().db_path)

    # 가장 최근 OHLCV 데이터 확인
    latest_timestamp = simple_data.get_latest_ohlcv_timestamp(coin_name)
    if latest_timestamp:
        latest_timestamp = datetime.datetime.strptime(latest_timestamp, "%Y-%m-%d %H:%M:%S")

    now = datetime.datetime.utcnow()
    if not latest_timestamp or latest_timestamp < now - datetime.timedelta(minutes=60):
        # 최신 데이터가 현재보다 오래된 경우 추가 데이터 로드
        start_date = latest_timestamp if latest_timestamp else now - datetime.timedelta(days=define_days)
        print(f"load start get_ohlcv_from {start_date}")
        df = pyupbit.get_ohlcv_from(ticker=coin_name, interval="minute60", fromDatetime=start_date)
        
        if df is not None and not df.empty:
            simple_data.insert_ohlcv_data(coin_name, df)
            print(f"✅ {coin_name} 데이터 업데이트 완료!")
        else:
            print(f"⚠ {coin_name} 데이터 가져오기 실패")

    # 최근 2년치 데이터 가져오기
    start_date = now - datetime.timedelta(days=define_days)
    end_date = now
    ohlcv_records = simple_data.get_ohlcv_data(coin_name, start_date, end_date)
    print(f"ohlcv_records {ohlcv_records}")

    # 1. 관찰 데이터 준비 (변동률과 거래량)
    observations = ohlcv_records[["price_change", "volume"]].dropna().values  # NaN 제거 후 numpy 배열로 변환

    # 2. HMM 모델 생성
    model = hmm.GaussianHMM(n_components=3, covariance_type="diag", n_iter=100)

    # 3. 모델 학습
    model.fit(observations)

    # 4. 숨겨진 상태 예측
    hidden_states = model.predict(observations)

    # 5. 출력
    print("Transition matrix:\n", model.transmat_)  # 전이 확률 행렬

    # Means 변환 (퍼센트로 출력)
    means = model.means_  # 각 상태의 평균
    means[:, 0] = means[:, 0] * 100  # 변동률 열(첫 번째 열)만 퍼센트로 변환

    print("Means of each hidden state (변환 후):")
    for i, mean in enumerate(means):
        print(f"State {i}: 변동률 평균 = {mean[0]:.5f}%, 거래량 평균 = {mean[1]:.5f}")
    
    # 숨겨진 상태 출력
    print("Hidden states:", hidden_states)

    # 6. 시장 상태 변화 예측
    current_state = hidden_states[-1]  # 가장 최근 상태
    print(f"\n현재 상태: State {current_state}")

    # 다음 상태 확률 계산
    next_state_probs = model.transmat_[current_state]
    for i, prob in enumerate(next_state_probs):
        print(f"State {current_state} -> State {i} 전환 확률: {prob:.2%}")

    stable_state, normal_state, volatile_state = classify_states(means)

    # 매수 신호 (안정 상태에서 급등 상태로 전이 확률 높음)
    buy_signal = current_state == stable_state and next_state_probs[volatile_state] > 0.2

    # 매도 신호 (급등 상태에서 안정 상태로 전이 확률 높음)
    sell_signal = current_state == volatile_state and next_state_probs[stable_state] > 0.3

    # 매매 신호 결정
    if buy_signal:
        print("📈 매수 신호: 상승 가능성 높음!")
    elif sell_signal:
        print("📉 매도 신호: 하락 가능성 높음!")
    else:
        print("⏸️ 보류: 명확한 매매 신호 없음")


