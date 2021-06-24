import csv
import itertools
from operator import itemgetter

# stockCodes = ["A069500", "A122630", "A114800", "A252670"]
stockCodes = ["A069500"]

def getOhlc(row):
    openPrice = int(row[0]["open"])
    maxHighPrice = int(row[0]["high"])
    minLowPrice = int(row[0]["low"])
    closePrice = int(row[len(row) - 1]["close"])

    for item in row:
        maxHighPrice = max(maxHighPrice, int(item["high"]))
        minLowPrice = min(minLowPrice, int(item["low"]))
    return {
        "openPrice": openPrice,
        "maxHighPrice": maxHighPrice,
        "minLowPrice": minLowPrice,
        "closePrice": closePrice
    }


for code in stockCodes:
    stockItemList = []
    with open("./data/" + code + ".csv", "r") as f:
        rdr = csv.DictReader(f)
        for item in rdr:
            stockItemList.append(item)
    print(code + " " + format(len(stockItemList), ","))

    groupByDate = {}

    for item in stockItemList:
        date = item["date"]
        dateList = groupByDate.get(date)

        if dateList == None:
            dateList = []
            groupByDate[date] = dateList

        dateList.append(item)

    for dateKey in groupByDate:
        row = groupByDate[dateKey]
        print(str(dateKey) + ": " + str(len(row)))

        ohlcValue = getOhlc(row)
        print(ohlcValue)

print("끝.")
