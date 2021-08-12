import os
import logging
value = {
    "slack": {
        "use": False,
        "token": os.getenv("slack-token"),
        "channel": "#boksl-trade"
    },
    "logger": {
        "file": "./boksl-trade.log",
        "level": logging.INFO,
        "format": "[%(asctime)s] %(levelname)s:%(message)s"
    },
    # 변동성 돌파전략 관련 설정
    "vbs": {
        # 매매 대상 종목. 동일 비중 매매
        # A122630 - KODEX 레버리지
        # A233740 - KODEX 코스닥150 레버리지
        # A069500 - KODEX 200
        # A229200 - KODEX 코스닥 150
        # "stockCode": ["A122630", "A233740"],
        "stockCode": ["A069500", "A229200"],
        # 현금 대비 투자 비중. 예: 1 = 100%, 0.5 = 50%
        "investRate": 0.99
    }
}
