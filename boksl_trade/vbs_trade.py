import ctypes
import sys
import time
import win32com.client
import pandas as pd
import requests
import config
from datetime import datetime
from log import logger
from tendo import singleton
from PyQt5.QtWidgets import *
from enum import Enum, auto


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


class StockInfo:
    """종목별 가격"""

    def __init__(
        self,
        code,
        name,
        openPrice,
        targetPrice,
    ):
        self.__code = code  # 종목코드
        self.__name = name  # 종목이름
        self.__openPrice = openPrice  # 시초가
        self.__targetPrice = targetPrice  # 매수목표가
        self.__currentPrice = 0  # 현재가
        self.__buy = False  # 매수 종목

    @property
    def code(self):
        return self.__code

    @property
    def name(self):
        return self.__name

    @property
    def openPrice(self):
        return self.__openPrice

    @property
    def currentPrice(self):
        return self.__currentPrice

    @property
    def targetPrice(self):
        return self.__targetPrice

    @currentPrice.setter
    def currentPrice(self, currentPrice):
        self.__currentPrice = currentPrice

    @property
    def buy(self):
        return self.__buy

    @buy.setter
    def buy(self, buy):
        self.__buy = buy

    def isBuyable(self):
        """매수 해되면 True, 아니면 False"""
        if not self.__buy:
            return False

        # 값이 초기화 되지 않았으면 매수 상태 아님
        if self.__targetPrice == 0 or self.__currentPrice == 0:
            return False

        return self.__targetPrice <= self.__currentPrice

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return '코드: {}, 이름: {}, 시초가: {:,},  현재가: {:,}, 목표가: {:,}, 매수여부: {})'.format(self.__code, self.__name, self.__openPrice, self.__currentPrice, self.__targetPrice, self.__buy)


class VbsTrade:
    """변동성 돌파전략 매매"""

    def __init__(self):
        self.__stockCurHandler = []
        self.__stockCodes = config.value["vbs"]["stockCode"]

        # <종목코드:가격정보>
        self.__stockInfoMap = {}

    @property
    def stockCodes(self):
        return self.__stockCodes

    def addEvent(self, stockCursor):
        """실시간 시세 핸들러 등록"""
        self.__stockCurHandler.append(stockCursor)

    def OnReceived(self):
        """시세 변경 이벤트 핸들러"""
        code = VbsTrade.instance.GetHeaderValue(0)  # 종목코드
        name = VbsTrade.instance.GetHeaderValue(1)  # 종목명
        time = VbsTrade.instance.GetHeaderValue(3)  # 시간
        timess = VbsTrade.instance.GetHeaderValue(18)  # 초
        exFlag = VbsTrade.instance.GetHeaderValue(19)  # 예상체결 플래그
        cprice = VbsTrade.instance.GetHeaderValue(13)  # 현재가
        diff = VbsTrade.instance.GetHeaderValue(2)  # 대비
        cVol = VbsTrade.instance.GetHeaderValue(17)  # 순간체결수량
        vol = VbsTrade.instance.GetHeaderValue(9)  # 거래량

        # 장중(체결)가가 아니면 무시
        if (exFlag != ord('2')):  # 동시호가 시간 (예상체결)
            return

        stockInfo = self.__stockInfoMap[code]
        stockInfo.currentPrice = cprice

        # TODO 아래 구문 삭제
        print("실시간(장중 체결)", timess, cprice, "대비", diff, "체결량", cVol, "거래량", vol)

        if stockInfo.isBuyable():
            buyCash = self.getBuyCash()

            # 매수
            if self.buyStock(stockInfo, buyCash):
                stockInfo.buy = True

            time.sleep(5)

    def getBuyCash(self):
        """매수 가격"""
        buyStockCount = 0
        for stockInfo in self.__stockInfoMap:
            if stockInfo.buy:
                buyStockCount += 1

        myCash = self.getCurrentCash()
        buyRate = ((buyStockCount + 1) / len(self.__stockInfoMap)) * config.value["vbs"]["investRate"]
        buyCash = myCash * buyRate
        return buyCash

    def initStockInfo(self):
        """종목 초기 정보 얻기"""
        for code in self.__stockCodes:
            stockName, stockQty, stockPrice, stockGain = self.getStockBalance(code)  # 종목명과 보유수량 조회
            openPrice, targetPrice = self.getTargetPrice(code)
            stockPrice = StockInfo(code, stockName, openPrice, targetPrice)
            self.__stockInfoMap[code] = stockPrice

    def sendTargetPrice(self):
        """종목별 코드별 매수 목표가 슬랙으로 전달"""
        messageArr = []
        for stockInfo in self.__stockInfoMap.values():
            messageArr.append(stockInfo.name + ", 시초가: {:,}, 매수 목표가: {:,}".format(stockInfo.openPrice, stockInfo.targetPrice))

        sendSlack("\n".join(messageArr))

    def getStockBalance(self, code):
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

    def getTargetPrice(self, code):
        """시초가와 매수 목표가를 반환한다."""
        try:
            time_now = datetime.now()
            str_today = time_now.strftime("%Y%m%d")
            ohlc = self.getOhlc(code, 10)

            # TODO 다시 원위치
            # if str_today == str(ohlc.iloc[0].name):
            openPrice = ohlc.iloc[0].open
            lastday = ohlc.iloc[1]
            # else:
            #     return None, None

            lastday_high = lastday[1]
            lastday_low = lastday[2]
            target_price = openPrice + (lastday_high - lastday_low) * config.value["vbs"]["k"]

            printlog("{:,} + ({:,} - {:,}) * {} = {:,}".format(openPrice, lastday_high, lastday_low, config.value["vbs"]["k"], target_price))

            # ETF는 호가 단위(5원)울 맞춰 줌
            targetPrice = int(target_price) - int(target_price) % 5
            return openPrice, targetPrice

        except Exception as ex:
            sendSlack("`getTargetPrice() -> exception! " + str(ex) + "`")
            raise ex

    def buyStock(self, stockInfo, buyCash):
        """
            인자로 받은 종목을 매수한다.

            stockInfo: 매수 종목
            buyCash: 매수가격
        """
        try:

            # 매수 수량
            buyQty = int(buyCash // stockInfo.targetPrice)

            acc = cpTradeUtil.AccountNumber[0]  # 계좌번호
            accFlag = cpTradeUtil.GoodsList(acc, 1)  # -1:전체,1:주식,2:선물/옵션

            # 매수 주문 설정
            cpOrder.SetInputValue(0, "2")  # 2: 매수
            cpOrder.SetInputValue(1, acc)  # 계좌번호
            cpOrder.SetInputValue(2, accFlag[0])  # 상품구분 - 주식 상품 중 첫번째
            cpOrder.SetInputValue(3, stockInfo.code)  # 종목코드
            cpOrder.SetInputValue(4, buyQty)  # 매수할 수량
            cpOrder.SetInputValue(5, stockInfo.targetPrice)  # 주문 단가
            cpOrder.SetInputValue(7, "0")  # 주문조건 0:기본, 1:IOC, 2:FOK
            cpOrder.SetInputValue(8, "01")  # 주문호가 01:지정가, 03:시장가, 5:조건부, 12:최유리, 13:최우선

            # 매수 주문 요청
            ret = cpOrder.BlockRequest()
            sendSlack("매수 요청 ->", stockInfo.stockName + "(" + stockInfo.code + ")", "수량: {:,}".format(buyQty),
                      "현재가격: {:,}".format(stockInfo.currentPrice), "주문가격: {:,}".format(stockInfo.targetPrice),  "->", ret)

            rqStatus = cpOrder.GetDibStatus()
            errMsg = cpOrder.GetDibMsg1()

            if ret != 0:
                raise Exception("주문요청 오류: " + str(ret) + " " + errMsg)

            if rqStatus != 0:
                raise Exception("주문 실패: " + str(rqStatus) + " " + errMsg)

            buy = True

            return buy
        except Exception as ex:
            sendSlack("`매수 실패 - " + stockInfo + " -> exception! " + str(ex) + "`")
            return False

    def getCurrentCash(self):
        """증거금 100% 주문 가능 금액을 반환한다."""
        try:
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
            return cash
        except Exception as ex:
            sendSlack("get_current_cash() -> exception! " + str(ex))
            raise ex

    def sendStatus(self):
        """종목별 코드 매수 상태를 슬랙으로 전달"""
        myCash = self.getCurrentCash()
        messageArr = []
        messageArr.append("보유 현금: {:,}".format(myCash))

        for stockInfo in self.__stockInfoMap.values():
            stockName, stockQty, stockPrice, stockGain = self.getStockBalance(stockInfo.code)  # 종목명과 보유수량 조회
            if stockQty == 0:
                messageArr.append(stockName + ",. 현재 보유 수량: {:,}".format(stockQty))
            else:
                messageArr.append(stockName + ",. 현재 보유 수량: {:,}, 평가금액: {:,}, 수익률: {:.2f}%".format(stockQty, stockPrice, stockGain))

        sendSlack("\n".join(messageArr))

    def getOhlc(self, code, qty):
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

    def getMovingaverage(self, code, window):
        """인자로 받은 종목에 대한 직전 거래일 이동평균가격을 반환한다."""
        try:
            timeNow = datetime.now()
            strToday = timeNow.strftime("%Y%m%d")
            ohlc = self.getOhlc(code, 20)
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

    def isOpenDay(self):
        """장이 열리는 요일 판단"""
        today = datetime.today().weekday()
        # 토요일이나 일요일이면 자동 종료
        if today == 5 or today == 6:
            return False

        return True

    def isGetableOpenPrice(self):
        """
        당일 시초가를 얻을 수 있는지를 판단
        시장이 열려서 목표가를 얻을 수 있는지 판단하기 위함
        """
        for code in self.stockCodes:
            openPrice = self.getTargetPrice(code)
            if openPrice == None:
                return False
        return True


class TradeTask:
    class __TradeStatus:
        def __init__(self):
            self.isLoadStock = False  # 매매 대상 종목 로드 여부

    def __init__(self):

        self.__stockCurList = []
        self.__isRq = False
        self.__vbsTrade = VbsTrade()
        self.__statusCheck = False
        self.__tradeStatus = TradeTask.__TradeStatus()

    def startSubscribe(self):
        """실시간 시세 조회 이벤트 등록"""
        for code in self.__vbsTrade.stockCodes:
            stockCur = win32com.client.Dispatch("DsCbo1.StockCur")
            stockCur.SetInputValue(0, code)
            self.__vbsTrade.addEvent(stockCur)
            stockCur.Subscribe()
            self.__stockCurList.append(stockCur)

        self.__isRq = True

    def stopSubscribe(self):
        """실시간 시세 조회 이벤트 중지"""
        if self.__isRq:
            for stockCur in self.__stockCurList:
                stockCur.Unsubscribe()
        self.__isRq = False

    def checkMarket(self):
        """
        마켓 상태 체크
        return True이면 프로그램 종료를 해야된다는 뜻
        """
        t_now = datetime.now()
        t_9 = t_now.replace(hour=9, minute=0, second=5, microsecond=0)
        t_start = t_now.replace(hour=9, minute=1, second=0, microsecond=0)
        t_sell = t_now.replace(hour=15, minute=20, second=0, microsecond=0)
        today = datetime.today().weekday()

        if not self.__tradeStatus.isLoadStock:
            self.__vbsTrade.initStockInfo()
            self.__tradeStatus.isLoadStock = True

        # TODO 아래 구문 주석 해제
        # if not self.__vbsTrade.isOpenDay():
        #     sendSlack("오늘은 주식 시장이 열리지 않았음")
        #     exit()
        # if t_sell < t_now:
        #     self.__vbsTrade.sendStatus()
        #     sendSlack("복슬매매 종료")
        #     return True

        if t_9 < t_now:
            sendSlack("복슬 매매 시작")
            if self.__vbsTrade.isGetableOpenPrice():
                printlog("아직 시초가 얻기전")
                return False
            printlog("시초가 얻음")

            self.__vbsTrade.initStockInfo()
            self.__vbsTrade.sendStatus()
            self.__statusCheck = True

    def exit(self):
        self.stopSubscribe()
        sys.exit(0)


if __name__ == "__main__":
    # 중복실행 방지
    me = singleton.SingleInstance()

    task = TradeTask()
    task.startSubscribe()
    try:
        while True:
            if task.checkMarket():
                break
            time.sleep(1)

    except Exception as ex:
        sendSlack("exception! " + str(ex))
        raise ex

# slack message 전달 대기 wait
time.sleep(5)

# try:
#     # printlog("시작 시간 :", datetime.now().strftime("%m/%d %H:%M:%S"))
#     # sendSlack("복슬 매매 시작")
#     # time.sleep(5)

#     # print("크래온 플러스 동작:", checkCreonSystem())

#     # targetStockCode = config.value["vbs"]["stockCode"]

#     # # 실시간 시세 조회
#     # for code in targetStockCode:
#     #     objStockCur.SetInputValue(0, code)
#     #     CpEvent.instance = objStockCur
#     #     # 하이닉스 실시간 현재가 요청
#     #     objStockCur.Subscribe()
#     # print("실시간 시세 조회 핸들러 등록")

#     a = VbsTrade()
#     a.initStockInfo()

# except Exception as ex:
#     sendSlack("exception! " + str(ex))
#     raise ex
