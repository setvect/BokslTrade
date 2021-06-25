import condition
from backtest_module import *

cond = condition.Condition(
    k=0.5,
    targetStock=[Stock("A069500", "KODEX 200", False)],
    investRatio=0.5,
    fromDate=20210112,
    toDate=20210623,
    cash=10000000,
    tradeMargin=5,
    feeBid=0.00015,
    feeAsk=0.00015,
    loseStopRate=0.003,
    gainStopRate=0.05,
    trailingStopRate=0.001,
    comment="횡보구간",
)

tradeHistory = backtestVbs(cond)
analysisResult = backtestAnalysis(cond, tradeHistory)
makeExcel(tradeHistory, cond, analysisResult)


print("끝.")
