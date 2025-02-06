import pyupbit
from hmmlearn import hmm
import numpy as np
from simple_common.simpledata import SimpleData
from config import ConfigInfo
import datetime
import time


def classify_states(means):
    """ 각 상태(State)를 변동률과 거래량을 기준으로 분류 """
    #변동률 오름차순으로 정리가 된다.
    #sorted_states [(2, array([-0.10370,  3300641.37828])), (0, array([0.41064, 908960.52486])), (1, array([3.85377, 16688833.84133]))]
    #이런식으로 정렬된다. array([-0.10370,  3300641.37828])) 이건 변동률 평균, 거래량 평균 순서.
    sorted_states = sorted(enumerate(means), key=lambda x: (x[1][0], x[1][1]))  # 변동률 기준 정렬

    
    print(f"[classify_states] sorted_states {sorted_states}")

    stable_state = sorted_states[0][0]  # 변동률이 가장 낮은 상태 (안정적인 시장)
    normal_state = sorted_states[1][0]  # 중간 변동성을 가진 상태
    volatile_state = sorted_states[2][0]  # 변동성이 가장 큰 상태 (급등/급락 시장)

    return stable_state, normal_state, volatile_state

def classify_states_way2(means):
    """
    각 상태를 변동률(첫 번째 값)을 기준으로 분류합니다.
    조건:
      - bullish_state: 양수들 중에서 변동률이 가장 높은 상태 (급등)
      - stable_state: 양수들 중에서 변동률이 가장 낮은 상태 (안정)
      - bearish_state: 음수들 중에서 변동률이 가장 낮은 상태 (급락)
    만약 양수나 음수가 존재하지 않으면, 나머지 그룹에서 0에 가까운 상태(절대값 기준)로 할당합니다.
    
    반환 순서는 (stable_state, bullish_state, bearish_state)
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
        # 급락 상태: 이미 bearish_state로 지정됨 (음수 중 가장 낮은 값)
        # 남은 하나를 bullish_state로 지정 (없다면 같은 값을 쓰지만, 중복되지 않도록 함)
        remaining = list(all_indices - {stable_state, bearish_state})
        if remaining:
            bullish_state = remaining[0]
        else:
            bullish_state = stable_state  # 극히 드문 경우
    # 만약 음수가 없다면(모두 양수):
    if not negative_indices:
        # 안정과 급등은 이미 양수 그룹에서 선정
        # 남은 하나를 bearish_state로 지정
        remaining = list(all_indices - {stable_state, bullish_state})
        if remaining:
            bearish_state = remaining[0]
        else:
            bearish_state = stable_state  # 극히 드문 경우

    # 만약 어떤 이유로 중복이 발생했다면 (예: 상태가 2개밖에 없는 경우) 남은 인덱스를 채워줌
    assigned = {stable_state, bullish_state, bearish_state}
    if len(assigned) < 3:
        missing = list(all_indices - assigned)
        if missing:
            # 중복된 항목 중 하나를 대체합니다.
            # 여기서는 우선 stable_state를 missing 값으로 바꾸도록 함
            stable_state = missing[0]

    if is_debug:
        print(f"[classify_states] 변동률: {rates}")
        print(f"안정 상태: {stable_state}, 상향 상태: {bullish_state}, 하양 상태: {bearish_state}")
    
    return stable_state, bullish_state, bearish_state

is_debug = False

def MainTest(isForce):
    # 데이터 가져오기
    coin_name = "KRW-XRP"
    define_days=365 #10일치
    is_check_time = False

    simple_data = SimpleData(ConfigInfo.Instance().db_path)

    # 기본 날짜 초기화.
    now = datetime.datetime.now()
    next_check_time = now - datetime.timedelta(minutes=1)

    # 가장 최근 OHLCV 데이터 확인
    latest_timestamp = simple_data.get_latest_ohlcv_timestamp(coin_name)
    if latest_timestamp:
        latest_timestamp = datetime.datetime.strptime(latest_timestamp, "%Y-%m-%d %H:%M:%S")
        next_check_time = latest_timestamp + datetime.timedelta(minutes=15)

    if is_debug:
        print(f"[CHECK TIME] latest_timestamp {latest_timestamp},  next_check_time : {next_check_time}, now :{now}")
    if not latest_timestamp or next_check_time <= now:
        # 최신 데이터가 현재보다 오래된 경우 추가 데이터 로드
        start_date = latest_timestamp if latest_timestamp else now - datetime.timedelta(days=define_days)
        if is_debug:
            print(f"load start get_ohlcv_from {start_date}")
        df = pyupbit.get_ohlcv_from(ticker=coin_name, interval="minute15", fromDatetime=start_date)
        
        if df is not None and not df.empty:
            simple_data.insert_ohlcv_data(coin_name, df)
            if is_debug:
                print(f"✅ {coin_name} 데이터 업데이트 완료!")
        else:
            if is_debug:
                print(f"⚠ {coin_name} 데이터 가져오기 실패")

        is_check_time = True

    if isForce:
        is_check_time = True

    if is_check_time:

        is_check_time = False
        # 최근 2년치 데이터 가져오기
        start_date = now - datetime.timedelta(days=define_days)
        end_date = now
        ohlcv_records = simple_data.get_ohlcv_data(coin_name, start_date, end_date)
        if is_debug:
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
        if is_debug:
            print("Transition matrix:\n", model.transmat_)  # 전이 확률 행렬

        # Means 변환 (퍼센트로 출력)
        means = model.means_  # 각 상태의 평균
        means[:, 0] = means[:, 0] * 100  # 변동률 열(첫 번째 열)만 퍼센트로 변환

        if is_debug:
            print(f"Means of each hidden state (변환 후): {means}")
            for i, mean in enumerate(means):
                print(f"State {i}: 변동률 평균 = {mean[0]:.5f}%, 거래량 평균 = {mean[1]:.5f}")
        
        
        # 숨겨진 상태 출력
        if is_debug:
            print("Hidden states:", hidden_states)

        # 6. 시장 상태 변화 예측
        current_state = hidden_states[-1]  # 가장 최근 상태
        if is_debug:
            print(f"\n현재 상태: State {current_state}")

        # 다음 상태 확률 계산
        next_state_probs = model.transmat_[current_state]
        if is_debug:
            print(f"다음 상태 확률 계산 \n {next_state_probs}")
            for i, prob in enumerate(next_state_probs):
                print(f"State {current_state} -> State {i} 전환 확률: {prob:.2%}")

        #stable_state, normal_state, volatile_state = classify_states(means)
        #각 상태를 변동률(첫 번째 값)을 기준으로 분류합니다.
        #- bullish_state: 변동률이 가장 높은 상태 (급등)
        #- bearish_state: 변동률이 가장 낮은 상태 (급락)
        #- stable_state: 변동률이 0에 가장 가까운 상태 (안정)
        bullish_state, bearish_state, stable_state = classify_states_way2(means)

        # 매수 신호 (안정 상태에서 급등 상태로 전이 확률 높음)
        buy_signal = current_state == stable_state and next_state_probs[bullish_state] > 0.2

        # 매도 신호 (급등 상태에서 안정 상태로 전이 확률 높음)
        sell_signal = current_state == bullish_state and next_state_probs[stable_state] > 0.3

        kst_now = datetime.datetime.now()
        str_kst_now = kst_now.strftime("%m/%d %H:%M:%S")
        # 매매 신호 결정
        if buy_signal:
            print(f"{str_kst_now} - 📈 매수 신호: 상승 가능성 높음!")
        elif sell_signal:
            print(f"{str_kst_now} - 📉 매도 신호: 하락 가능성 높음!")
        else:
            print(f"{str_kst_now} - ⏸️ 보류: 명확한 매매 신호 없음")

if __name__ == '__main__':

    print("테스트 시작!!")
    is_first = True
    while True:
        try:
            MainTest(is_first)
        except Exception as e:
            print(e)

        is_first = False
        time.sleep(60)
