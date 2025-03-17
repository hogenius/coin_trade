import pyupbit
import datetime
from simple_common.simpledata import SimpleData
from hmmlearn import hmm
import numpy as np
from config import ConfigInfo

def classify_states_way2(means):
    """
    각 상태를 변동률(첫 번째 값)을 기준으로 분류합니다.
    조건:
      - bullish_state: 양수들 중에서 변동률이 가장 높은 상태 (급등)
      - stable_state: 양수들 중에서 변동률이 가장 낮은 상태 (안정)
      - bearish_state: 음수들 중에서 변동률이 가장 낮은 상태 (급락)
    """
    rates = means[:, 0]
    num_states = len(rates)
    all_indices = set(range(num_states))
    
    # 양수와 음수 인덱스 구분
    positive_indices = [i for i, r in enumerate(rates) if r > 0]
    negative_indices = [i for i, r in enumerate(rates) if r < 0]
    
    # 초기값 None
    bullish_state = None
    stable_state = None
    bearish_state = None

    # 양수가 존재하면: 안정, 급등은 양수 그룹에서 선정
    if positive_indices:
        bullish_state = max(positive_indices, key=lambda i: rates[i])
        stable_state = min(positive_indices, key=lambda i: rates[i])
    # 음수가 존재하면: 급락은 음수 그룹에서 선정
    if negative_indices:
        bearish_state = min(negative_indices, key=lambda i: rates[i])
    
    # 만약 양수가 없다면(모두 음수):
    if not positive_indices:
        # 안정 상태: 0에 가까운 음수 (즉, 가장 큰 값)
        stable_state = max(negative_indices, key=lambda i: rates[i])
        # 남은 하나를 bullish_state로 지정
        remaining = list(all_indices - {stable_state, bearish_state})
        if remaining:
            bullish_state = remaining[0]
        else:
            bullish_state = stable_state
    # 만약 음수가 없다면(모두 양수):
    if not negative_indices:
        # 남은 하나를 bearish_state로 지정
        remaining = list(all_indices - {stable_state, bullish_state})
        if remaining:
            bearish_state = remaining[0]
        else:
            bearish_state = stable_state

    # 만약 어떤 이유로 중복이 발생했다면 남은 인덱스를 채워줌
    assigned = {stable_state, bullish_state, bearish_state}
    if len(assigned) < 3:
        missing = list(all_indices - assigned)
        if missing:
            stable_state = missing[0]

    return stable_state, bullish_state, bearish_state

def check_buy_hmm(coin_info, balances, config, simple_data:SimpleData, print_msg, isForce, isTest):
    """
    HMM을 사용하여 매수 시점을 체크하는 함수
    """
    coin_name = coin_info['name']
    # if isTest:
    #     print_msg(f"check_buy_hmm {coin_name} 체크 시작합니다.")
    define_days = 365  # 1년치 데이터

    # 가장 최근 OHLCV 데이터 확인
    latest_timestamp = simple_data.get_latest_ohlcv_timestamp(coin_name)
    if latest_timestamp:
        latest_timestamp = datetime.datetime.strptime(latest_timestamp, "%Y-%m-%d %H:%M:%S")

    is_update = False
    now = datetime.datetime.now()
    # print_msg(f"latest_timestamp : {latest_timestamp}, now : {now}")
    if not latest_timestamp or latest_timestamp < now - datetime.timedelta(minutes=15):
        # 최신 데이터가 현재보다 오래된 경우 추가 데이터 로드
        start_date = latest_timestamp if latest_timestamp else now - datetime.timedelta(days=define_days)
        if isTest:
            print_msg(f"udpate start get_ohlcv_from {start_date}")
        df = pyupbit.get_ohlcv_from(ticker=coin_name, interval="minute15", fromDatetime=start_date)
        
        if df is not None and not df.empty:
            simple_data.insert_ohlcv_data(coin_name, df)
            if isTest:
                print_msg(f"{coin_name} 데이터 업데이트 완료!")
            is_update = True
        else:
            if isTest:
                print_msg(f"{coin_name} 데이터 가져오기 실패")
            return False

    if is_update == False :
        return False
    
    # 최근 데이터 가져오기
    start_date = now - datetime.timedelta(days=define_days)
    end_date = now
    ohlcv_records = simple_data.get_ohlcv_data(coin_name, start_date, end_date)

    # 관찰 데이터 준비 (변동률과 거래량)
    observations = ohlcv_records[["price_change", "volume"]].dropna().values

    # HMM 모델 생성 및 학습
    model = hmm.GaussianHMM(n_components=3, covariance_type="diag", n_iter=100)
    model.fit(observations)

    # 숨겨진 상태 예측
    hidden_states = model.predict(observations)
    current_state = hidden_states[-1]  # 가장 최근 상태

    # 다음 상태 확률 계산
    next_state_probs = model.transmat_[current_state]

    # 상태 분류
    means = model.means_
    means[:, 0] = means[:, 0] * 100  # 변동률을 퍼센트로 변환
    stable_state, bullish_state, bearish_state = classify_states_way2(means)

    current_state_text = "unknown 상태"
    if current_state == stable_state:
        current_state_text = "안정 상태"
    elif current_state == bullish_state:
        current_state_text = "불(상승) 상태"
    elif current_state == bearish_state:
        current_state_text = "베어(하락) 상태"
    else:
        current_state_text = "알 수 없음"

    arr_send_msg = []
    # 매수 신호 조건
    buy_signal = current_state == stable_state and next_state_probs[bullish_state] > 0.2

    if buy_signal:
        arr_send_msg.append(f"{coin_name} 매수 신호: 상승 가능성 높음!")
        arr_send_msg.append(f" 현재 상태: {current_state} / {current_state_text}, 급등 상태 전이 확률: {next_state_probs[bullish_state]:.2%}")
        print_msg(" ".join(arr_send_msg))
    else :
        if isTest:
            arr_send_msg.append(f"{coin_name} 매수 신호 없음..")
            arr_send_msg.append(f" 현재 상태: {current_state} / {current_state_text}, 급등 상태 전이 확률: {next_state_probs[bullish_state]:.2%}")
            print_msg(" ".join(arr_send_msg))

    return buy_signal

    