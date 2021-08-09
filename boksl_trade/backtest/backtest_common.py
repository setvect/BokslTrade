import csv

# 종목별 분봉 데이터 가져옴
def loadPriceDate(code):
    stockItemList = []
    with open("../../data/5_minute/" + code + ".csv", "r") as f:
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
