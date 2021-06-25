import csv
import sys
import xlsxwriter
import util
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
    date = priceList[0]["date"]
    openPrice = priceList[0]["open"]
    maxHighPrice = priceList[0]["high"]
    minLowPrice = priceList[0]["low"]
    closePrice = priceList[len(priceList) - 1]["close"]

    for item in priceList:
        maxHighPrice = max(maxHighPrice, item["high"])
        minLowPrice = min(minLowPrice, item["low"])
    return {
        "date": date,
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


def backtestVbs(stockItemList, cond):
    groupByDate = getGroupByDate(stockItemList)

    # 일단위 OHLC 구함
    for dateKey in groupByDate:
        ohlc = getOhlc(groupByDate[dateKey])

    tradeHistory = []

    currentDate = None
    beforeOhlc = None

    targetValue = sys.maxsize

    beforeTrade = TradeResult(cash=cond.cash)
    currentTrade = None

    for candle in stockItemList:
        if currentDate != candle["date"]:
            if currentDate is not None:
                if currentTrade is not None:
                    beforeTrade = currentTrade
                    if not (currentDate < cond.fromDate or currentDate > cond.toDate):
                        tradeHistory.append(currentTrade)
                beforeOhlc = getOhlc(groupByDate[currentDate])
                currentTrade = TradeResult()
                currentTrade.cash = beforeTrade.getFinalResult()
                currentTrade.beforeClose = beforeOhlc["close"]
                currentTrade.candle = candle

                # 매수 목표가 구하기
                targetValue = candle["open"] + int(
                    (beforeOhlc["high"] - beforeOhlc["low"]) * cond.k
                )
                currentTrade.targetPrice = targetValue
            currentDate = candle["date"]

        # 직전 캔들 데이터가 없으면 skip
        if beforeOhlc is None:
            continue

        # 백테스팅 대상 범위가 아니면 skip
        if currentDate < cond.fromDate or currentDate > cond.toDate:
            continue

        # 매수 했다면 매도 조건 체크
        if currentTrade.isTrade:
            rate = candle["close"] / currentTrade.bidPrice - 1
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
                currentTrade.askPrice = candle["close"] - cond.tradeMargin
                currentTrade.feePrice = (
                    currentTrade.feePrice
                    + (currentTrade.askPrice * currentTrade.volume) * cond.feeAsk
                )

        # 매수 체크
        elif isBidTime(candle["time"]):
            if currentTrade.targetPrice > candle["close"]:
                continue

            currentTrade.candle = getOhlc(groupByDate[currentDate])
            currentTrade.bidPrice = candle["close"] + cond.tradeMargin

            # 매수 가능 금액
            possible = int(beforeTrade.getFinalResult() * cond.investRatio)
            # 매수 가능 수량
            currentTrade.volume = possible // currentTrade.bidPrice

            currentTrade.feePrice = currentTrade.getBidAmount() * cond.feeBid
            currentTrade.cash = (
                beforeTrade.getFinalResult() - currentTrade.getBidAmount()
            )
            # print(
            #     "매수 {}:{} 목표가: {:,}, 단가:{:,}, 수량:{:,}, 총금액: {:,} ".format(
            #         candle["date"],
            #         candle["time"],
            #         currentTrade.targetPrice,
            #         currentTrade.bidPrice,
            #         currentTrade.volume,
            #         currentTrade.getBidAmount(),
            #     )
            # )

            currentTrade.isTrade = True

    if currentTrade is not None:
        tradeHistory.append(currentTrade)

    return tradeHistory


# 백테스팅 분석
def backtestAnalysis(cond, tradeHistory):
    # 주식 수익률, MDD
    stockPriceList = [trade.candle["close"] for trade in tradeHistory]
    stockPriceList.insert(0, tradeHistory[0].candle["open"])
    stockYield = util.getYield(stockPriceList)
    stockMdd = util.getMdd(stockPriceList)

    # 투자 수익률, MDD
    realPriceList = [trade.getFinalResult() for trade in tradeHistory]
    realPriceList.insert(0, cond.cash)
    realYield = util.getYield(realPriceList)
    realMdd = util.getMdd(realPriceList)

    result = {
        "stockYield": stockYield,
        "stockMdd": stockMdd,
        "realYield": realYield,
        "realMdd": realMdd,
    }
    return result


# 백테스팅 결과 엑셀 파일 만들기
def makeExcel(tradeHistory, cond):
    workbook = xlsxwriter.Workbook(
        "backtest_result/{}_{}.xlsx".format(cond.fromDate, cond.toDate)
    )
    worksheet = workbook.add_worksheet("result")
    worksheet.set_row(
        0, None, workbook.add_format({"bold": True, "align": "center", "border": 1})
    )

    style1 = workbook.add_format({"num_format": "#,###", "border": 1})
    worksheet.set_column("B:F", None, style1)
    worksheet.set_column("I:I", None, style1)
    worksheet.set_column("K:K", None, style1)
    worksheet.set_column("M:M", None, style1)
    worksheet.set_column("O:O", None, style1)
    worksheet.set_column("R:W", None, style1)

    style2 = workbook.add_format({"num_format": "0.00%", "border": 1})
    worksheet.set_column("G:G", None, style2)
    worksheet.set_column("H:H", None, style2)
    worksheet.set_column("N:N", None, style2)
    worksheet.set_column("Q:Q", None, style2)

    style3 = workbook.add_format({"border": 1})
    worksheet.set_column("A:A", None, style3)
    worksheet.set_column("J:J", None, style3)
    worksheet.set_column("L:L", None, style3)
    worksheet.set_column("P:P", None, style3)

    bg1 = workbook.add_format({"bg_color": "#e1e4ed"})
    bg2 = workbook.add_format({"bg_color": "#dbe1f5"})
    bg3 = workbook.add_format({"bg_color": "#fde9d9"})

    header = [
        "날짜",
        "시가",
        "고가",
        "저가",
        "종가",
        "직전 종가",
        "당일 수익률",
        "장중 수익률",
        "매수 목표가",
        "매매여부",
        "매수 체결 가격",
        "트레일링 스탑 진입 여부",
        "매수 수량",
        "최고수익률",
        "매도 체결 가격",
        "매도 이유",
        "실현 수익률",
        "투자금",
        "현금",
        "투자 수익",
        "수수료",
        "투자 결과",
        "현금+투자결과-수수료",
    ]
    for idx, name in enumerate(header):
        worksheet.write(0, idx, name)

    for idx, trade in enumerate(tradeHistory, 1):
        worksheet.write(idx, 0, trade.candle["date"])
        worksheet.write(idx, 1, trade.candle["open"])
        worksheet.write(idx, 2, trade.candle["high"])
        worksheet.write(idx, 3, trade.candle["low"])
        worksheet.write(idx, 4, trade.candle["close"])
        worksheet.write(idx, 5, trade.beforeClose)
        worksheet.write(idx, 6, trade.getCandleYield())
        worksheet.write(idx, 7, trade.getMarketYield())
        worksheet.write(idx, 8, trade.targetPrice)
        worksheet.write(idx, 9, trade.isTrade)
        worksheet.write(idx, 10, trade.bidPrice)
        worksheet.write(idx, 11, trade.isTrailing)
        worksheet.write(idx, 12, trade.volume)
        worksheet.write(idx, 13, trade.highYield)
        worksheet.write(idx, 14, trade.askPrice)
        worksheet.write(
            idx, 15, trade.askReason.name if trade.askReason is not None else "-"
        )
        worksheet.write(idx, 16, trade.getRealYield())
        worksheet.write(idx, 17, trade.getBidAmount())
        worksheet.write(idx, 18, trade.cash)
        worksheet.write(idx, 19, trade.getGains())
        worksheet.write(idx, 20, trade.feePrice)
        worksheet.write(idx, 21, trade.getInvestResult())
        worksheet.write(idx, 22, trade.getFinalResult())

    workbook.close()


cond = condition.Condition(
    k=0.5,
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
)

# A069500: KODEX 200
# A122630: KODEX 레버리지
# A114800: KODEX 인버스
# A252670: KODEX 200선물인버스2X
stockItemList = loadPriceDate("A069500")
tradeHistory = backtestVbs(stockItemList, cond)
result = backtestAnalysis(cond, tradeHistory)

print(
    "주식수익률: {:.2f}%, 주식MDD: {:.2f}%, 투자수익률: {:.2f}%, 투자MDD: {:.2f}%".format(
        result["stockYield"], result["stockMdd"], result["realYield"], result["realMdd"]
    )
)

makeExcel(tradeHistory, cond)
print("끝.")
