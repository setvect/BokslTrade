import os
import sys
import ctypes
import time
import win32com.client
import pandas as pd
from datetime import datetime


# 크레온 플러스 공통 OBJECT
cpCodeMgr = win32com.client.Dispatch("CpUtil.CpStockCode")
cpStatus = win32com.client.Dispatch("CpUtil.CpCybos")
cpTradeUtil = win32com.client.Dispatch("CpTrade.CpTdUtil")
cpStock = win32com.client.Dispatch("DsCbo1.StockMst")
cpOhlc = win32com.client.Dispatch("CpSysDib.StockChart")
cpBalance = win32com.client.Dispatch("CpTrade.CpTd6033")
cpCash = win32com.client.Dispatch("CpTrade.CpTdNew5331A")
cpOrder = win32com.client.Dispatch("CpTrade.CpTd0311")

# 매매 대상 종목
# A122630 - KODEX 레버리지
# A233740 - KODEX 코스닥150 레버리지
targetStockCode = ["A122630", "A233740"]


def dbgout(message):
    """인자로 받은 문자열을 파이썬 셸과 슬랙으로 동시에 출력한다."""
    print(datetime.now().strftime("[%m/%d %H:%M:%S]"), message)
    strbuf = datetime.now().strftime("[%m/%d %H:%M:%S] ") + message
    # slack.chat.post_message("#etf-algo-trading", strbuf)


def printlog(message, *args):
    """인자로 받은 문자열을 파이썬 셸에 출력한다."""
    print(datetime.now().strftime("[%m/%d %H:%M:%S]"), message, *args)


def check_creon_system():
    """크레온 플러스 시스템 연결 상태를 점검한다."""
    # 관리자 권한으로 프로세스 실행 여부
    if not ctypes.windll.shell32.IsUserAnAdmin():
        printlog("check_creon_system() : admin user -> FAILED")
        return False

    # 연결 여부 체크
    if cpStatus.IsConnect == 0:
        printlog("check_creon_system() : connect to server -> FAILED")
        return False

    # 주문 관련 초기화 - 계좌 관련 코드가 있을 때만 사용
    if cpTradeUtil.TradeInit(0) != 0:
        printlog("check_creon_system() : init trade -> FAILED")
        return False
    return True


def get_current_price(code):
    """인자로 받은 종목의 현재가, 매도호가, 매수호가를 반환한다."""
    cpStock.SetInputValue(0, code)  # 종목코드에 대한 가격 정보
    cpStock.BlockRequest()
    item = {}
    item["cur_price"] = cpStock.GetHeaderValue(11)  # 현재가
    item["ask"] = cpStock.GetHeaderValue(16)  # 매도호가
    item["bid"] = cpStock.GetHeaderValue(17)  # 매수호가
    return item["cur_price"], item["ask"], item["bid"]


def get_ohlc(code, qty):
    """인자로 받은 종목의 OHLC 가격 정보를 qty 개수만큼 반환한다."""
    cpOhlc.SetInputValue(0, code)  # 종목코드
    cpOhlc.SetInputValue(1, ord("2"))  # 1:기간, 2:개수
    cpOhlc.SetInputValue(4, qty)  # 요청개수
    cpOhlc.SetInputValue(5, [0, 2, 3, 4, 5])  # 0:날짜, 2~5:OHLC
    cpOhlc.SetInputValue(6, ord("D"))  # D:일단위
    cpOhlc.SetInputValue(9, ord("1"))  # 0:무수정주가, 1:수정주가
    cpOhlc.BlockRequest()
    count = cpOhlc.GetHeaderValue(3)  # 3:수신개수
    columns = ["open", "high", "low", "close"]
    index = []
    rows = []
    for i in range(count):
        index.append(cpOhlc.GetDataValue(0, i))
        rows.append(
            [
                cpOhlc.GetDataValue(1, i),
                cpOhlc.GetDataValue(2, i),
                cpOhlc.GetDataValue(3, i),
                cpOhlc.GetDataValue(4, i),
            ]
        )
    df = pd.DataFrame(rows, columns=columns, index=index)
    return df


def get_stock_balance(code):
    """인자로 받은 종목의 종목명과 수량을 반환한다."""
    cpTradeUtil.TradeInit()
    acc = cpTradeUtil.AccountNumber[0]  # 계좌번호
    accFlag = cpTradeUtil.GoodsList(acc, 1)  # -1:전체, 1:주식, 2:선물/옵션
    cpBalance.SetInputValue(0, acc)  # 계좌번호
    cpBalance.SetInputValue(1, accFlag[0])  # 상품구분 - 주식 상품 중 첫번째
    cpBalance.SetInputValue(2, 50)  # 요청 건수(최대 50)
    cpBalance.BlockRequest()
    if code == "ALL":
        dbgout("계좌명: " + str(cpBalance.GetHeaderValue(0)))
        dbgout("결제잔고수량 : " + str(cpBalance.GetHeaderValue(1)))
        dbgout("평가금액: " + str(cpBalance.GetHeaderValue(3)))
        dbgout("평가손익: " + str(cpBalance.GetHeaderValue(4)))
        dbgout("종목수: " + str(cpBalance.GetHeaderValue(7)))
    stocks = []
    for i in range(cpBalance.GetHeaderValue(7)):
        stock_code = cpBalance.GetDataValue(12, i)  # 종목코드
        stock_name = cpBalance.GetDataValue(0, i)  # 종목명
        stock_qty = cpBalance.GetDataValue(15, i)  # 수량
        if code == "ALL":
            dbgout(str(i + 1) + " " + stock_code + "(" + stock_name + ")" + ":" + str(stock_qty))

            stocks.append({"code": stock_code, "name": stock_name, "qty": stock_qty})
        if stock_code == code:
            return stock_name, stock_qty
    if code == "ALL":
        return stocks
    else:
        stock_name = cpCodeMgr.CodeToName(code)
        return stock_name, 0


def get_current_cash():
    """증거금 100% 주문 가능 금액을 반환한다."""
    cpTradeUtil.TradeInit()
    acc = cpTradeUtil.AccountNumber[0]  # 계좌번호
    accFlag = cpTradeUtil.GoodsList(acc, 1)  # -1:전체, 1:주식, 2:선물/옵션
    cpCash.SetInputValue(0, acc)  # 계좌번호
    cpCash.SetInputValue(1, accFlag[0])  # 상품구분 - 주식 상품 중 첫번째
    cpCash.BlockRequest()
    return cpCash.GetHeaderValue(9)  # 증거금 100% 주문 가능 금액


def get_target_price(code):
    """매수 목표가를 반환한다."""
    try:
        time_now = datetime.now()
        str_today = time_now.strftime("%Y%m%d")
        ohlc = get_ohlc(code, 10)
        if str_today == str(ohlc.iloc[0].name):
            today_open = ohlc.iloc[0].open
            lastday = ohlc.iloc[1]
        else:
            raise Exception("거래 정보가 없습니다.")
        lastday_high = lastday[1]
        lastday_low = lastday[2]
        target_price = today_open + (lastday_high - lastday_low) * 0.5
        # ETF는 호가 단위가 5원
        askPrice = int(target_price) - int(target_price) % 5
        return askPrice

    except Exception as ex:
        dbgout("`get_target_price() -> exception! " + str(ex) + "`")
        return None


def buy_etf(code):
    """인자로 받은 종목을 최유리 지정가 FOK 조건으로 매수한다."""
    try:

        stock_name, stock_qty = get_stock_balance(code)  # 종목명과 보유수량 조회

        if stock_qty != 0:
            printlog("매수 물량 존재:" + stock_name + str(stock_qty))
            return

        targetPrice = get_target_price(code)  # 매수 목표가
        cash = get_current_cash()
        useCash = cash / len(targetStockCode)
        # 매수 수량
        buy_qty = int(useCash // targetPrice)

        printlog("매수 주문", stock_name + "(" + str(code) + "), 수량:" + str(buy_qty) + ", 가격: " + str(targetPrice))
        cpTradeUtil.TradeInit()
        acc = cpTradeUtil.AccountNumber[0]  # 계좌번호
        accFlag = cpTradeUtil.GoodsList(acc, 1)  # -1:전체,1:주식,2:선물/옵션

        # 최유리 FOK 매수 주문 설정
        cpOrder.SetInputValue(0, "2")  # 2: 매수
        cpOrder.SetInputValue(1, acc)  # 계좌번호
        cpOrder.SetInputValue(2, accFlag[0])  # 상품구분 - 주식 상품 중 첫번째
        cpOrder.SetInputValue(3, code)  # 종목코드
        cpOrder.SetInputValue(4, buy_qty)  # 매수할 수량
        cpOrder.SetInputValue(5, targetPrice)  # 주문 단가
        cpOrder.SetInputValue(7, "0")  # 주문조건 0:기본, 1:IOC, 2:FOK
        cpOrder.SetInputValue(8, "01")  # 주문호가 01:지정가, 03:시장가
        # 5:조건부, 12:최유리, 13:최우선
        # 매수 주문 요청
        ret = cpOrder.BlockRequest()
        printlog("매수 요청 ->", stock_name, code, buy_qty, targetPrice,  "->", ret)

        if ret != 0:
            printlog("주문요청 오류", ret)

        rqStatus = cpOrder.GetDibStatus()
        errMsg = cpOrder.GetDibMsg1()
        if rqStatus != 0:
            printlog("주문 실패: ", rqStatus, errMsg)

        time.sleep(2)
    except Exception as ex:
        dbgout("`buy_etf(" + str(code) + ") -> exception! " + str(ex) + "`")


def get_movingaverage(code, window):
    """인자로 받은 종목에 대한 직전 거래일 이동평균가격을 반환한다."""
    try:
        time_now = datetime.now()
        str_today = time_now.strftime("%Y%m%d")
        ohlc = get_ohlc(code, 20)
        if str_today == str(ohlc.iloc[0].name):
            lastday = ohlc.iloc[1].name
        else:
            lastday = ohlc.iloc[0].name
        closes = ohlc["close"].sort_index()
        ma = closes.rolling(window=window).mean()
        return ma.loc[lastday]
    except Exception as ex:
        dbgout("get_movingavrg(" + str(window) + ") -> exception! " + str(ex))
        return None


stockCode = "A122630"

print(check_creon_system())
# print(get_current_price(buyEtf))
# ohlc = get_ohlc(buyEtf, 10)
# print(ohlc)
print(get_current_cash())

print(get_stock_balance(stockCode))

targetPrice = get_target_price(stockCode)
printlog("매수 목표가:" + str(targetPrice))

buy_etf(stockCode)

# ma5 = get_movingaverage(buyEtf, 5)
# printlog("5일 이동평균:" + str(ma5))
