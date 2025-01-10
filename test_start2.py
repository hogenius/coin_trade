import pyupbit
from hmmlearn import hmm
import numpy as np

if __name__ == '__main__':
    # 데이터 가져오기
    df = pyupbit.get_ohlcv("KRW-BTC", "minute60", 999)

    # 변동률 계산
    df["price_change"] = df["close"].pct_change() * 100  # 변동률 계산 (퍼센트)

    # 1. 관찰 데이터 준비 (변동률과 거래량)
    observations = df[["price_change", "volume"]].dropna().values  # NaN 제거 후 numpy 배열로 변환

    # 2. HMM 모델 생성
    model = hmm.GaussianHMM(n_components=6, covariance_type="diag", n_iter=100)

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