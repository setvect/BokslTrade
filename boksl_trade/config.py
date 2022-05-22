import logging
value = {
    # 슬랙
    "slack": {
        # 슬랙 메시지 전달 사용 여부
        "use": False,
        # 슬랙 토큰
        "token": "xoxb-xxxxxxxx",
        # 채널명
        "channel": "#my-channel"
    },
    # 로깅
    "logger": {
        "file": "./boksl-trade.log",
        "level": logging.INFO,
        "format": "[%(asctime)s] %(levelname)s:%(message)s"
    },
    # 변동성 돌파전략 관련 설정
    "vbs": {
        # 전일 기준 변동성 돌파 비율
        # 매수 목표가: 오늘 시가 + (전일 고가 - 전일 저가) * k
        "k": 0.5,

        # 현금 대비 투자 비중. 예: 1 = 100%, 0.5 = 50%
        "investRate": 0.99,

        # 매매 대상 종목. 동일 비중 매매
        # A122630 - KODEX 레버리지
        # A233740 - KODEX 코스닥150 레버리지
        # A069500 - KODEX 200
        # A229200 - KODEX 코스닥 150
        # A091170 - KODEX 은행
        # "stockCode": ["A122630", "A233740"],
        # "stockCode": ["A069500", "A229200"],
        "stockCode": ["A233740", "A091170"],
    }
}
