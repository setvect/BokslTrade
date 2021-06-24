import csv
import sys
import condition
from trade_result import AskReason, TradeResult


# 종목별 분봉 데이터 가져옴
def loadPriceDate(code):
    stockItemList = []
    with open("./data/" + code + ".csv", "r") as f:
        rdr = csv.DictReader(f)
        for item in rdr:
            item["date"] = int(item["date"])
            item["time"] = int(item["time"])
            item["open"] = int(item["open"])
            item["high"] = int(item["high"])
            item["low"] = int(item["low"])
            item["close"] = int(item["close"])
            item["volume"] = int(item["volume"])
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
    openPrice = priceList[0]["open"]
    maxHighPrice = priceList[0]["high"]
    minLowPrice = priceList[0]["low"]
    closePrice = priceList[len(priceList) - 1]["close"]

    for item in priceList:
        maxHighPrice = max(maxHighPrice, item["high"])
        minLowPrice = min(minLowPrice, item["low"])
    return {
        "open": openPrice,
        "high": maxHighPrice,
        "low": minLowPrice,
        "close": closePrice,
    }


# 매수 시간 확인
def isBidTime(time):
    return 910 < time < 1500


# 매도 가능 시간
def isAskTime(time):
    return 1510 < time < 1520


cond = condition.Condition(
    k=0.5,
    investRatio=0.5,
    fromDate=20190701,
    toDate=20191231,
    cash=10000000,
    tradeMargin=5,
    feeBid=0.0005,
    feeAsk=0.0005,
    loseStopRate=0.002,
    gainStopRate=0.02,
)

# stockCodes = ["A069500", "A122630", "A114800", "A252670"]

stockItemList = loadPriceDate("A069500")
groupByDate = getGroupByDate(stockItemList)

# 일단위 OHLC 구함
for dateKey in groupByDate:
    ohlc = getOhlc(groupByDate[dateKey])
    # print(dateKey + ": " + str(ohlc))

currentDate = None
beforeOhlc = None

targetValue = sys.maxsize
tradeHistory = []

beforeTrade = TradeResult(cash=cond.cash)
currentTrade = None

for candle in stockItemList:
    if currentDate != candle["date"]:
        if currentDate is not None:
            if currentTrade is not None:
                beforeTrade = currentTrade
                tradeHistory.append(currentTrade)
            beforeOhlc = getOhlc(groupByDate[currentDate])
            currentTrade = TradeResult()
            currentTrade.beforeClose = beforeOhlc["close"]

            # 매수 목표가 구하기
            targetValue = candle["open"] + int(
                (beforeOhlc["high"] - beforeOhlc["low"]) * cond.k
            )

            print(
                "{date} 매수 목표가 = 시초가: {open:,} + (전일고가: {high:,} * 전일저가: {low:,}) * K: {k:,} = {targetValue:,}".format(
                    date=candle["date"],
                    open=beforeOhlc["open"],
                    high=beforeOhlc["high"],
                    low=beforeOhlc["low"],
                    k=cond.k,
                    targetValue=targetValue,
                )
            )
            currentTrade.targetPrice = targetValue
            # print(
            #     "chage date:",
            #     currentDate,
            #     ", targetValue:",
            #     format(targetValue, ","),
            # )

        currentDate = candle["date"]

    # 직전 캔들 데이터가 없으면 skip
    if beforeOhlc is None:
        continue

    # 백테스팅 대상 범위가 아니면 skip
    if currentDate < cond.fromDate or currentDate > cond.toDate:
        continue

    # 매수 했다면 매도 조건 체크
    if currentTrade.trade:
        rate = currentTrade.bidPrice / candle["close"] - 1
        currentTrade.highYield = max(
            currentTrade.highYield,
            rate,
        )

        if currentTrade.askPrice != 0:
            continue

        askReason = None

        # 매도 시간 경과
        if isAskTime(candle["time"]):
            askReason = AskReason.TIME
        # 손절 체크
        elif -rate > cond.loseStopRate:
            askReason = AskReason.LOSS
        # 익절 체크
        elif rate > cond.gainStopRate:
            askReason = AskReason.GAIN

        if askReason is not None:
            currentTrade.askReason = askReason
            currentTrade.askPrice = candle["close"]
            currentTrade.feePrice = (
                currentTrade.feePrice
                + (currentTrade.askPrice * currentTrade.volume) * cond.feeAsk
            )

    # 매수 체크
    elif isBidTime(candle["time"]):
        if currentTrade.targetPrice > candle["close"]:
            continue

        currentTrade.candle = getOhlc(groupByDate[currentDate])
        currentTrade.bidPrice = candle["close"]

        # 매수 가능 금액
        possible = int(beforeTrade.getFinalResult() * cond.investRatio)
        # 매수 가능 수량
        currentTrade.volume = possible // candle["close"]

        currentTrade.feePrice = currentTrade.getInvestmentAmount() * cond.feeBid
        currentTrade.cash = (
            beforeTrade.getFinalResult() - currentTrade.getInvestmentAmount()
        )

        currentTrade.trade = True

if currentTrade is not None:
    tradeHistory.append(currentTrade)

print("끝.")
