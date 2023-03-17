import csv
import win32com.client
import datetime
import time
import os

fieldNames = ["date", "time", "open", "high", "low", "close", "volume"]


def getMarketPrice(objStockMst, code, dateFrom, dateTo):
    fieldKeys = [0, 1, 2, 3, 4, 5, 8]
    dictChart = {name: [] for name in fieldNames}

    objStockMst.SetInputValue(0, code)
    objStockMst.SetInputValue(1, ord("1"))  # 0: 개수, 1: 기간
    objStockMst.SetInputValue(3, dateFrom)  # 시작일
    objStockMst.SetInputValue(2, dateTo)  # 종료일
    objStockMst.SetInputValue(4, 1)  # 요청 개수
    objStockMst.SetInputValue(5, fieldKeys)  # 필드
    objStockMst.SetInputValue(6, ord("m"))  # "D", "W", "M", "m", "T"
    objStockMst.SetInputValue(7, 5)  # 5분봉
    objStockMst.SetInputValue(9, ord("1"))  # 0: 무수정, 1: 수정주가
    objStockMst.BlockRequest()
    status = objStockMst.GetDibStatus()
    msg = objStockMst.GetDibMsg1()
    print("통신상태: {} {}".format(status, msg))

    if status != 0:
        print("통신 불량")
        exit()

    cnt = objStockMst.GetHeaderValue(3)  # 수신개수
    marketPrice = []

    for i in range(cnt):
        dict_item = {
            name: objStockMst.GetDataValue(pos, i)
            for pos, name in zip(range(len(fieldNames)), fieldNames)
        }
        for k, v in dict_item.items():
            dictChart[k].append(v)

        marketPrice.append(dict_item)
    return reversed(marketPrice)


objCpCybos = win32com.client.Dispatch("CpUtil.CpCybos")
bConnect = objCpCybos.IsConnect
if bConnect == 0:
    print("PLUS가 정상적으로 연결되지 않음. ")
    exit()


# 현재가 객체 구하기
objStockMst = win32com.client.Dispatch("CpSysDib.StockChart")

# A069500: KODEX 200
# A122630: KODEX 레버리지
# A114800: KODEX 인버스
# A252670: KODEX 200선물인버스2X
# A233740: KODEX 코스닥150 레버리지
# A091170: KODEX 은행
# stockCodes = ["A069500", "A122630", "A114800", "A252670"]
# stockCodes = ["A233740", "A091170"]
stockCodes = ["A091170", "A233740"]

# marketPrice = getMarketPrice(objStockMst, "A069500", "20200706", "20200706")
# for item in marketPrice:
#     print(item.values())

toDate = datetime.datetime.now()
dirName = "./data/5_minute_" + toDate.strftime("%Y%m%d") + "/"
if not os.path.exists(dirName):
    os.makedirs(dirName)
    print(f"디렉토리 만듦 '{dirName}'")

for code in stockCodes:
    # fromDate = toDate - datetime.timedelta(days=365 * 5 + 50)
    fromDate = datetime.datetime(2023, 1, 7)

    with open(dirName + code + ".csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(fieldNames)

        while fromDate <= toDate:
            dateFormat = fromDate.strftime("%Y%m%d")
            weekday = fromDate.weekday()
            fromDate = fromDate + datetime.timedelta(days=1)
            # 토요일, 일요일 skip
            if weekday == 5 or weekday == 6:
                continue

            marketPrice = getMarketPrice(objStockMst, code, dateFormat, dateFormat)
            for item in marketPrice:
                w.writerow(item.values())

            print(dateFormat + " 수집")
            time.sleep(0.25)
print("끝.")
