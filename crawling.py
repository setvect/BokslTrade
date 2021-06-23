import win32com.client

objCpCybos = win32com.client.Dispatch("CpUtil.CpCybos")
bConnect = objCpCybos.IsConnect
if (bConnect == 0):
    print("PLUS가 정상적으로 연결되지 않음. ")
    exit()

# 현재가 객체 구하기
objStockMst = win32com.client.Dispatch("CpSysDib.StockChart")
list_field_key = [0, 1, 2, 3, 4, 5, 8]
list_field_name = ['date', 'time', 'open', 'high', 'low', 'close', 'volume']
dict_chart = {name: [] for name in list_field_name}

# A069500: KODEX 200
# A122630: KODEX 레버리지
# A114800: KODEX 인버스
# A252670: KODEX 200선물인버스2X
objStockMst.SetInputValue(0, "A069500")
objStockMst.SetInputValue(1, ord('1'))  # 0: 개수, 1: 기간
objStockMst.SetInputValue(3, 20210623)  # 시작일
objStockMst.SetInputValue(2, 20210623)  # 종료일
objStockMst.SetInputValue(4, 100)  # 요청 개수
objStockMst.SetInputValue(5, list_field_key)  # 필드
objStockMst.SetInputValue(6, ord('m'))  # 'D', 'W', 'M', 'm', 'T'
objStockMst.BlockRequest()
status = objStockMst.GetDibStatus()
msg = objStockMst.GetDibMsg1()
print("통신상태: {} {}".format(status, msg))

if status != 0:
  print("통신 불량")
  exit()

cnt = objStockMst.GetHeaderValue(3)  # 수신개수
for i in range(cnt):
    dict_item = {name: objStockMst.GetDataValue(
        pos, i) for pos, name in zip(range(len(list_field_name)), list_field_name)}
    for k, v in dict_item.items():
        dict_chart[k].append(v)

    print(dict_item)

print("끝.")
