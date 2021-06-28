import condition
from backtest_module import *
from backtest_common import *

rangeList = [
    # (20200120, 20200319, "하락장"),
    # (20200120, 20200805, "하락후 복귀"),
    # (20200319, 20210111, "상승장"),
    # (20210112, 20210623, "횡보장"),
    # (20190625, 20210623, "2년기간"),
]

cond = condition.Condition(
    targetStock=[Stock("A069500", "KODEX 200", False)],
    investRatio=0.5,
    fromDate=20210101,
    toDate=20211230,
    cash=10000000,
    tradeMargin=5,
    feeBuy=0.00015,
    feeSell=0.00015,
    upBuyRate=0.000,
    downSellRate=0.000,
    shortMalDuration=1,
    longMalDuration=20,
    comment="최근1개월",
)

tradeHistory = backtestMal(cond)
analysisResult = backtestAnalysis(cond, tradeHistory)
makeExcel(tradeHistory, cond, analysisResult)

print("끝.")
