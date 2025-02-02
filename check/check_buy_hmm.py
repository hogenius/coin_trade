import pyupbit
import datetime
from simple_common.simpledata import SimpleData
from hmmlearn import hmm
       
def check_buy_hmm(coin_info, balances, config, simple_data:SimpleData, print_msg, isForce, isTest):
    coin_name = coin_info['name']

    # 가장 최근 OHLCV 데이터 확인
    latest_timestamp = simple_data.get_latest_ohlcv_timestamp(coin_name)
    if latest_timestamp:
        latest_timestamp = datetime.datetime.strptime(latest_timestamp, "%Y-%m-%d %H:%M:%S")

    now = datetime.datetime.utcnow()
    if not latest_timestamp or latest_timestamp < now - datetime.timedelta(minutes=60):
        # 최신 데이터가 현재보다 오래된 경우 추가 데이터 로드
        start_date = latest_timestamp if latest_timestamp else now - datetime.timedelta(days=2*365)
        df = pyupbit.get_ohlcv_from(ticker=coin_name, interval="minute60", fromDatetime=start_date)
        
        if df is not None and not df.empty:
            simple_data.insert_ohlcv_data(coin_name, df)
            print_msg(f"✅ {coin_name} 데이터 업데이트 완료!")
        else:
            print_msg(f"⚠ {coin_name} 데이터 가져오기 실패")

    # 최근 2년치 데이터 가져오기
    start_date = now - datetime.timedelta(days=2*365)
    end_date = now
    ohlcv_records = simple_data.get_ohlcv_data(coin_name, start_date, end_date)


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

    return False

    