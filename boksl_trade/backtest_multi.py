import condition
from backtest_module import *


# A069500: KODEX 200
# A122630: KODEX 레버리지
# A114800: KODEX 인버스
# A252670: KODEX 200선물인버스2X


def backtestRange(fromDate, toDate, comment):
    cond = condition.Condition(
        targetStock=[Stock("A069500", "KODEX 200", False)],
        investRatio=0.5,
        fromDate=fromDate,
        toDate=toDate,
        cash=10000000,
        tradeMargin=5,
        feeBuy=0.00015,
        feeSell=0.00015,
        upBuyRate=0.001,
        downSellRate=0.01,
        shortMalDuration=10,
        longMalDuration=20,
        comment=comment,
    )

    tradeHistory = backtestMal(cond)
    analysisResult = backtestAnalysis(cond, tradeHistory)
    makeExcel(tradeHistory, cond, analysisResult)
    return cond, analysisResult


rangeList = [
    (20200120, 20200319, "하락장"),
    (20200120, 20200805, "하락후 복귀"),
    (20200319, 20210111, "상승장"),
    (20210112, 20210623, "횡보장"),
    (20190625, 20210623, "2년기간"),
]

resultList = []

for r in rangeList:
    cond, analysisResult = backtestRange(r[0], r[1], r[2])
    resultList.append({"condition": cond, "analysisResult": analysisResult})


makeAnalysisExcel(resultList)

print("끝.")
