import csv
import win32com.client
fieldNames = ["date", "time", "open", "high", "low", "close", "volume"]


def getMarketPrice(objStockMst, code):
    fieldKeys = [0, 1, 2, 3, 4, 5, 8]
    dictChart = {name: [] for name in fieldNames}

    # A069500: KODEX 200
    # A122630: KODEX 레버리지
    # A114800: KODEX 인버스
    # A252670: KODEX 200선물인버스2X
    objStockMst.SetInputValue(0, code)
    objStockMst.SetInputValue(1, ord("1"))  # 0: 개수, 1: 기간
    objStockMst.SetInputValue(3, "20190624")  # 시작일
    objStockMst.SetInputValue(2, "20190624")  # 종료일
    objStockMst.SetInputValue(4, 1)  # 요청 개수
    objStockMst.SetInputValue(5, fieldKeys)  # 필드
    objStockMst.SetInputValue(6, ord("m"))  # "D", "W", "M", "m", "T"
    objStockMst.BlockRequest()
    status = objStockMst.GetDibStatus()
    msg = objStockMst.GetDibMsg1()
    print("통신상태: {} {}".format(status, msg))

    if status != 0:
        print("통신 불량")
        exit()

    cnt = objStockMst.GetHeaderValue(3)  # 수신개수
    accList = []

    for i in range(cnt):
        dict_item = {name: objStockMst.GetDataValue(
            pos, i) for pos, name in zip(range(len(fieldNames)), fieldNames)}
        for k, v in dict_item.items():
            dictChart[k].append(v)

        accList.append(dict_item)
    return accList


objCpCybos = win32com.client.Dispatch("CpUtil.CpCybos")
bConnect = objCpCybos.IsConnect
if (bConnect == 0):
    print("PLUS가 정상적으로 연결되지 않음. ")
    exit()


# 현재가 객체 구하기
objStockMst = win32com.client.Dispatch("CpSysDib.StockChart")

code = "A069500"
accList = getMarketPrice(objStockMst, code)

with open("./data/"+code+".csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(fieldNames)
    for item in accList:
        w.writerow(item.values())

# print(accList)

print("끝.")
