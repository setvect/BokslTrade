import condition
from backtest_module import *

rangeList = [
    # (20200120, 20200319, "하락장"),
    # (20200120, 20200805, "하락후 복귀"),
    # (20200319, 20210111, "상승장"),
    # (20210112, 20210623, "횡보장"),
    # (20190625, 20210623, "2년기간"),
]


# cond = condition.Condition(
#     k=0.5,
#     targetStock=[Stock("A069500", "KODEX 200", False)],
#     investRatio=0.5,
#     fromDate=20210112,
#     toDate=20210623,
#     cash=10000000,
#     tradeMargin=5,
#     feeBid=0.00015,
#     feeAsk=0.00015,
#     loseStopRate=0.002,
#     gainStopRate=0.003,
#     trailingStopRate=0.001,
#     comment="횡보구간",
# )

# cond = condition.Condition(
#     k=0.5,
#     targetStock=[Stock("A069500", "KODEX 200", False)],
#     investRatio=0.5,
#     fromDate=20200120,
#     toDate=20200805,
#     cash=10000000,
#     tradeMargin=5,
#     feeBid=0.00015,
#     feeAsk=0.00015,
#     loseStopRate=0.002,
#     gainStopRate=0.003,
#     trailingStopRate=0.001,
#     comment="하락후 복귀",
# )
cond = condition.Condition(
    k=0.5,
    targetStock=[Stock("A069500", "KODEX 200", False)],
    investRatio=0.5,
    fromDate=20190625,
    toDate=20210623,
    cash=10000000,
    tradeMargin=5,
    feeBid=0.00015,
    feeAsk=0.00015,
    loseStopRate=0.005,
    gainStopRate=0.01,
    trailingStopRate=0.001,
    comment="최근1개월",
)

tradeHistory = backtestVbs(cond)
analysisResult = backtestAnalysis(cond, tradeHistory)
makeExcel(tradeHistory, cond, analysisResult)


print("끝.")
