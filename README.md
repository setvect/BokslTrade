# 복슬매매
주식 자동 매매 프로그램입니다. 대신증권 `크래온 PLUS` API 활용해 시세 데이터를 클로링 합니다.
크롤링한 데이터를 이용해 이동평균선 돌파 전략으로 매매를 수행합니다.

## 파일 설명
- `boksl_trade/crawling.py`: 1분봉 데이터 크롤링 - 최근 2년치 데이터만 크레온 PLUS에서 제공합니다.
- 백테스트
  - `boksl_trade/backtest_single.py`: 하나의 조건 테스트. 일일 매도/매수 내역이 엑셀파일 출력
  - `boksl_trade/backtest_multi.py`: 여러 조건별로 요약결과가 제공. 조건별 투자 수익률, MDD 결과가 엑셀파일로 출력
- `boksl_trade/backtest_module.py`: 변동성 돌파 전략 알고리즘
- `test/slack.py`: Slack 메시지 전달

## 백테스트 조건
- 변동성 돌파 판단 비율
- 대상종목
- 총 현금을 기준으로 투자 비율. 1은 전액, 0.5은 50% 투자
- 분석대상 기간 - 시작
- 분석대상 기간 - 종료
- 최초 투자금액
- 매매시 채결 가격 차이
- 매수 수수료
- 매도 수수료
- 상승 매수률
- 하락 매도률
- 단기 이동평균 기간
- 장기 이동평균 기간
- 조건에대한 설명글

※ 관련 소스코드 `condition.py` 참고

## 매매 조건
### 매수 조건
아래 조건을 모두 만족해야 매수가 됨

- 직전 영업일 기준 매수 돌파가 없어야 함
- 단기 이동평균값 - 단기 이동평균값 * 상승 매수률 >= 장기 이동평균

예시)
- 단기 이동평균값: 10,000
- 장기 이동편균값: 9,800
- 상승 매수률: 0.01

  ```
  10,000 - 10,000 * 0.01 >= 9,800
  = 9,900 >= 9,800
  => 매수
  ```
### 매도 조건
아래 조건을 모두 만족해야 매수가 됨

- 매수 상태여야함
- 단기 이동평균값 + 단기 이동평균값 * 하락 매도률 <= 장기 이동평균

예시)
- 단기 이동평균값: 9,700
- 장기 이동편균값: 10,000
- 상승 매수률: 0.02

  ```
  9,700 + 9,700 * 0.02 <= 10,000
  = 9,894 <= 10,000
  => 매도
  ```

## 시세 클로링 데이터
### 1분봉 2019.6.25 ~ 2021.6.24
- `data/1_minute/A069500.csv`: KODEX 200
- `data/1_minute/A114800.csv`: KODEX 레버리지
- `data/1_minute/A122630.csv`: KODEX 인버스
- `data/1_minute/A252670.csv`: KODEX 200선물인버스2X
### 2분봉 2016.6.29 ~ 2021.6.28
- `data/5_minute/A069500.csv`: KODEX 200
- `data/5_minute/A114800.csv`: KODEX 레버리지
- `data/5_minute/A122630.csv`: KODEX 인버스
- `data/5_minute/A252670.csv`: KODEX 200선물인버스2X

## 참고
- [크래온플러스 API](https://money2.creontrade.com/e5/mboard/ptype_basic/HTS_Plus_Helper/DW_Basic_List_Page.aspx?boardseq=284&m=9505&p=8841&v=8643)
- [파이썬 증권 데이터 분석](https://github.com/INVESTAR/StockAnalysisInPython)
- [조코딩](https://www.youtube.com/watch?v=Y01D2J_7894&list=PLU9-uwewPMe0fB60VIMuKFV7gPDXmyOzp&index=1&ab_channel=%EC%A1%B0%EC%BD%94%EB%94%A9JoCoding)