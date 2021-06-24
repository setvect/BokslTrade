import csv
import sys
import condition
from trade_result import TradeResult


# 종목별 분봉 데이터 가져옴
def loadPriceDate(code):
    stockItemList = []
    with open("./data/" + code + ".csv", "r") as f:
        rdr = csv.DictReader(f)
        for item in rdr:
            stockItemList.append(item)
    print(code + " " + format(len(stockItemList), ","))
    return stockItemList


# 날짜 기준으로 그룹핑
def getGroupByDate(stockItemList):
    groupByDate = {}

    # 날짜로 group by
    for item in stockItemList:
        date = item["date"]
        dateList = groupByDate.get(date)

        if dateList == None:
            dateList = []
            groupByDate[date] = dateList

        dateList.append(item)
    return groupByDate


# 그룹 기준 OHLC 구하기
def getOhlc(priceList):
    openPrice = int(priceList[0]["open"])
    maxHighPrice = int(priceList[0]["high"])
    minLowPrice = int(priceList[0]["low"])
    closePrice = int(priceList[len(priceList) - 1]["close"])

    for item in priceList:
        maxHighPrice = max(maxHighPrice, int(item["high"]))
        minLowPrice = min(minLowPrice, int(item["low"]))
    return {
        "open": openPrice,
        "high": maxHighPrice,
        "low": minLowPrice,
        "close": closePrice,
    }


cond = condition.Condition(
    k=0.5,
    investRatio=0.5,
    fromDate="20190701",
    toDate="20191231",
    cash=10000000,
    tradeMargin=5,
    feeBid=0.0005,
    feeAsk=0.0005,
    loseStopRate=0.002,
    gainStopRate=0.02,
)

result = TradeResult()

# stockCodes = ["A069500", "A122630", "A114800", "A252670"]
stockCodes = ["A069500"]

for code in stockCodes:
    stockItemList = loadPriceDate(code)
    groupByDate = getGroupByDate(stockItemList)

    # 일단위 OHLC 구함
    for dateKey in groupByDate:
        ohlc = getOhlc(groupByDate[dateKey])
        # print(dateKey + ": " + str(ohlc))

    currentDate = None
    beforeOhlc = None

    targetValue = sys.maxsize
    for item in stockItemList:
        if currentDate != item["date"]:
            if currentDate is not None:
                beforeOhlc = getOhlc(groupByDate[currentDate])

                # 매수 목표가 구하기
                targetValue = int(item["open"]) + int(
                    (beforeOhlc["high"] - beforeOhlc["low"]) * cond.k
                )
                print(
                    "chage date:",
                    currentDate,
                    ", targetValue:",
                    format(targetValue, ","),
                )
            currentDate = item["date"]

        # 백테스팅 대상 범위가 아니면 skip
        if currentDate < cond.fromDate or currentDate > cond.toDate:
            continue

        print("check: " + str(item))


print("끝.")
