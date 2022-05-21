import ctypes
import time
import win32com.client
import pandas as pd
import requests
from datetime import datetime
import config
from log import logger
from tendo import singleton

# 크레온 플러스 공통 OBJECT
cpCodeMgr = win32com.client.Dispatch("CpUtil.CpStockCode")
cpStatus = win32com.client.Dispatch("CpUtil.CpCybos")
cpTradeUtil = win32com.client.Dispatch("CpTrade.CpTdUtil")
cpStock = win32com.client.Dispatch("DsCbo1.StockMst")
cpOhlc = win32com.client.Dispatch("CpSysDib.StockChart")
cpBalance = win32com.client.Dispatch("CpTrade.CpTd6033")
cpCash = win32com.client.Dispatch("CpTrade.CpTdNew5331A")
cpOrder = win32com.client.Dispatch("CpTrade.CpTd0311")

# 매수요청한 종목 코드
buyRequsetStockCode = set()


def sendSlack(*messageArgs):
    message = ' '.join(list(map(str, messageArgs)))

    """인자로 받은 문자열을 파이썬 셸과 슬랙으로 동시에 출력한다."""
    printlog("Send Slack: " + message)

    if not config.value["slack"]["use"]:
        return

    sendMessage = datetime.now().strftime("[%m/%d %H:%M:%S] ") + message
    requests.post(
        "https://slack.com/api/chat.postMessage",
        headers={"Authorization": "Bearer " + config.value["slack"]["token"]},
        data={"channel": config.value["slack"]["channel"], "text": sendMessage},
    )


def printlog(message, *args):
    """인자로 받은 문자열을 파이썬 셸에 출력한다."""
    # print(datetime.now().strftime("[%m/%d %H:%M:%S]"), message, *args)
    logMessage = message + ' '.join(list(map(str, args)))
    logger.info(logMessage)


def checkCreonSystem():
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


def getCurrentPrice(code):
    """인자로 받은 종목의 현재가, 매도호가, 매수호가를 반환한다."""
    cpStock.SetInputValue(0, code)  # 종목코드에 대한 가격 정보
    cpStock.BlockRequest()
    item = {}
    item["cur_price"] = cpStock.GetHeaderValue(11)  # 현재가
    item["ask"] = cpStock.GetHeaderValue(16)  # 매도호가
    item["bid"] = cpStock.GetHeaderValue(17)  # 매수호가
    return item["cur_price"], item["ask"], item["bid"]


def getOhlc(code, qty):
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


def getStockBalance(code):
    """인자로 받은 종목의 종목명, 수량, 평가금액, 수익률을 반환한다."""
    cpTradeUtil.TradeInit()
    acc = cpTradeUtil.AccountNumber[0]  # 계좌번호
    accFlag = cpTradeUtil.GoodsList(acc, 1)  # -1:전체, 1:주식, 2:선물/옵션
    cpBalance.SetInputValue(0, acc)  # 계좌번호
    cpBalance.SetInputValue(1, accFlag[0])  # 상품구분 - 주식 상품 중 첫번째
    cpBalance.SetInputValue(2, 50)  # 요청 건수(최대 50)
    cpBalance.BlockRequest()

    for i in range(cpBalance.GetHeaderValue(7)):
        stockCode = cpBalance.GetDataValue(12, i)  # 종목코드
        name = cpBalance.GetDataValue(0, i)  # 종목명
        qty = cpBalance.GetDataValue(15, i)  # 수량
        price = cpBalance.GetDataValue(9, i)  # 평가금액
        gain = cpBalance.GetDataValue(11, i)  # 수익률
        if stockCode == code:
            return name, qty, price, gain
    else:
        name = cpCodeMgr.CodeToName(code)
        return name, 0, 0, 0


def getCurrentCash():
    """증거금 100% 주문 가능 금액을 반환한다."""
    try:
        time.sleep(1)
        cpTradeUtil.TradeInit()
        acc = cpTradeUtil.AccountNumber[0]  # 계좌번호
        accFlag = cpTradeUtil.GoodsList(acc, 1)  # -1:전체, 1:주식, 2:선물/옵션
        cpCash.SetInputValue(0, acc)  # 계좌번호
        cpCash.SetInputValue(1, accFlag[0])  # 상품구분 - 주식 상품 중 첫번째
        ret = cpCash.BlockRequest()
        if ret != 0:
            printlog("증거금 조회 오류", ret)
            return 0

        rqStatus = cpOrder.GetDibStatus()
        errMsg = cpOrder.GetDibMsg1()
        if rqStatus != 0:
            printlog("증거금 조회 실패: ", rqStatus, errMsg)
            return 0

        # 증거금 100% 주문 가능 금액
        cash = cpCash.GetHeaderValue(9)
        printlog("증거금: {:,}".format(cash))
        return cash
    except Exception as ex:
        sendSlack("get_current_cash() -> exception! " + str(ex))
        raise ex


# 오늘
def getTargetPrice(code):
    """매수 목표가를 반환한다."""
    try:
        time_now = datetime.now()
        str_today = time_now.strftime("%Y%m%d")
        ohlc = getOhlc(code, 10)
        if str_today == str(ohlc.iloc[0].name):
            today_open = ohlc.iloc[0].open
            lastday = ohlc.iloc[1]
        else:
            return None
        lastday_high = lastday[1]
        lastday_low = lastday[2]
        target_price = today_open + (lastday_high - lastday_low) * config.value["vbs"]["k"]

        printlog("{:,} + ({:,} - {:,}) * {} = {:,}".format(today_open, lastday_high, lastday_low, config.value["vbs"]["k"], target_price))

        # ETF는 호가 단위(5원)울 맞춰 줌
        askPrice = int(target_price) - int(target_price) % 5
        return askPrice

    except Exception as ex:
        sendSlack("`getTargetPrice() -> exception! " + str(ex) + "`")
        raise ex


def sendStatus(codeList):
    """종목별 코드 매수 상태를 슬랙으로 전달"""
    myCash = getCurrentCash()
    messageArr = []
    messageArr.append("보유 현금: {:,}".format(myCash))

    for code in codeList:
        stockName, stockQty, stockPrice, stockGain = getStockBalance(code)  # 종목명과 보유수량 조회
        if stockQty == 0:
            messageArr.append(stockName + ", 현재 보유 수량: {:,}".format(stockQty))
        else:
            messageArr.append(stockName + ", 현재 보유 수량: {:,}, 평가금액: {:,}, 수익률: {:.2f}%".format(stockQty, stockPrice, stockGain))

    sendSlack("\n".join(messageArr))


def sendTargetPrice(codeList):
    """종목별 코드별 매수 목표가 슬랙으로 전달"""
    messageArr = []
    for code in codeList:
        stockName, stockQty, stockPrice, stockGain = getStockBalance(code)  # 종목명과 보유수량 조회
        targetPrice = getTargetPrice(code)  # 매수 목표가
        if targetPrice is None:
            messageArr.append(stockName + ", 시장이 열리지 않았음")
        else:
            ohlc = getOhlc(code, 10)
            today_open = ohlc.iloc[0].open
            messageArr.append(stockName + ", 시초가: {:,}, 매수 목표가: {:,}".format(today_open, targetPrice))

    sendSlack("\n".join(messageArr))


def buyStock(codeList, myCash):
    """인자로 받은 종목을 매수한다."""
    try:
        buy = False
        buyStockCount = 0
        for code in codeList:
            stockName, stockQty, stockPrice, stockGain = getStockBalance(code)  # 종목명과 보유수량 조회
            if stockQty != 0:
                buyStockCount += 1

        buyRate = ((buyStockCount + 1) / len(codeList)) * config.value["vbs"]["investRate"]
        # 종목당 매수 제한 금액
        buyCash = myCash * buyRate

        for code in codeList:
            if code in buyRequsetStockCode:
                printlog("매수 요청 종목:", code)
                continue

            # TODO 상태가 변경될 때만 요청하도록 변경
            stockName, stockQty, stockPrice, stockGain = getStockBalance(code)  # 종목명과 보유수량 조회

            if stockQty != 0:
                printlog("매수 물량 존재:", stockName, str(stockQty))
                continue

            targetPrice = getTargetPrice(code)  # 매수 목표가
            if targetPrice is None:
                printlog("시장 열리지 않음")
                continue

            currentPrice, askPrice, bidPrice = getCurrentPrice(code)
            # 목표가를 돌파했을 경우 매수
            if currentPrice < targetPrice:
                printlog("목표가 돌파 못함 ", stockName + "(" + code + ")", "현재가: {:,}".format(currentPrice), "목표가: {:,}".format(targetPrice))
                continue

            # 매수 수량
            buyQty = int(buyCash // targetPrice)

            printlog("매수 주문", stockName + "(" + str(code) + "), 수량:" + str(buyQty) + ", 가격: " + str(targetPrice))
            cpTradeUtil.TradeInit()
            acc = cpTradeUtil.AccountNumber[0]  # 계좌번호
            accFlag = cpTradeUtil.GoodsList(acc, 1)  # -1:전체,1:주식,2:선물/옵션

            # API 단위 시간당 호출 건수 제한에 걸리지 않기 위해 일정시간 대기 후 매수 요청
            time.sleep(3)

            buyPrice = targetPrice
            # 매수 주문 설정
            cpOrder.SetInputValue(0, "2")  # 2: 매수
            cpOrder.SetInputValue(1, acc)  # 계좌번호
            cpOrder.SetInputValue(2, accFlag[0])  # 상품구분 - 주식 상품 중 첫번째
            cpOrder.SetInputValue(3, code)  # 종목코드
            cpOrder.SetInputValue(4, buyQty)  # 매수할 수량
            cpOrder.SetInputValue(5, buyPrice)  # 주문 단가
            cpOrder.SetInputValue(7, "0")  # 주문조건 0:기본, 1:IOC, 2:FOK
            cpOrder.SetInputValue(8, "01")  # 주문호가 01:지정가, 03:시장가, 5:조건부, 12:최유리, 13:최우선

            # 매수 주문 요청
            ret = cpOrder.BlockRequest()
            sendSlack("매수 요청 ->", stockName + "(" + code + ")", "수량: {:,}".format(buyQty), "매도호가: {:,}".format(askPrice), "주문가격: {:,}".format(buyPrice),  "->", ret)

            rqStatus = cpOrder.GetDibStatus()
            errMsg = cpOrder.GetDibMsg1()

            if ret != 0:
                raise Exception("주문요청 오류: " + str(ret) + " " + errMsg)

            if rqStatus != 0:
                raise Exception("주문 실패: " + str(rqStatus) + " " + errMsg)

            buy = True
            time.sleep(2)

            buyRequsetStockCode.add(code)
        return buy
    except Exception as ex:
        sendSlack("`buyStock(" + str(codeList) + ") -> exception! " + str(ex) + "`")
        time.sleep(2)
        return False


def sellStock(codeList):
    """보유한 모든 종목을 최유리 지정가 IOC 조건으로 매도한다."""
    try:
        cpTradeUtil.TradeInit()
        acc = cpTradeUtil.AccountNumber[0]  # 계좌번호
        accFlag = cpTradeUtil.GoodsList(acc, 1)  # -1:전체, 1:주식, 2:선물/옵션

        for code in codeList:
            stockName, stockQty, stockPrice, stockGain = getStockBalance(code)  # 종목명과 보유수량 조회
            if stockQty == 0:
                continue

            currentPrice, askPrice, bidPrice = getCurrentPrice(code)

            # 매도 채결을 위해 매수 호가 10원 내려서 주문
            sellPrice = bidPrice - 10
            cpOrder.SetInputValue(0, "1")  # 1:매도, 2:매수
            cpOrder.SetInputValue(1, acc)  # 계좌번호
            cpOrder.SetInputValue(2, accFlag[0])  # 주식상품 중 첫번째
            cpOrder.SetInputValue(3, code)  # 종목코드
            cpOrder.SetInputValue(4, stockQty)  # 매도수량
            cpOrder.SetInputValue(5, sellPrice)  # 주문 단가
            cpOrder.SetInputValue(7, "0")  # 조건 0:기본, 1:IOC, 2:FOK
            cpOrder.SetInputValue(8, "01")  # 주문호가 01:지정가, 03:시장가, 5:조건부, 12:최유리, 13:최우선
            ret = cpOrder.BlockRequest()
            sendSlack("매도 요청 ->", stockName + "(" + code + ")", "수량: {:,}".format(stockQty), "매수호가: {:,}".format(bidPrice), "주문가격: {:,}".format(sellPrice),  "결과:", ret)

            rqStatus = cpOrder.GetDibStatus()
            errMsg = cpOrder.GetDibMsg1()
            if ret != 0:
                raise Exception("주문요청 오류: " + str(ret) + " " + errMsg)

            if rqStatus != 0:
                raise Exception("주문 실패: " + str(rqStatus) + " " + errMsg)

            time.sleep(2)
    except Exception as ex:
        sendSlack("sellStock() -> exception! " + str(ex))
        time.sleep(2)
        raise ex


def getMovingaverage(code, window):
    """인자로 받은 종목에 대한 직전 거래일 이동평균가격을 반환한다."""
    try:
        timeNow = datetime.now()
        strToday = timeNow.strftime("%Y%m%d")
        ohlc = getOhlc(code, 20)
        if strToday == str(ohlc.iloc[0].name):
            lastday = ohlc.iloc[1].name
        else:
            lastday = ohlc.iloc[0].name
        closes = ohlc["close"].sort_index()
        ma = closes.rolling(window=window).mean()
        return ma.loc[lastday]
    except Exception as ex:
        sendSlack("get_movingavrg(" + str(window) + ") -> exception! " + str(ex))
        raise ex


def isOpenMarket():
    """장이 열리는 요일 판단"""
    t_now = datetime.now()
    today = datetime.today().weekday()
    # 토요일이나 일요일이면 자동 종료
    if today == 5 or today == 6:
        return False

    return True


if __name__ == "__main__":
    # 중복실행 방지
    me = singleton.SingleInstance()

    a = getOhlc("A069500", 1)
    print(a)
