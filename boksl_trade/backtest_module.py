from os import write
from re import T
import sys
import xlsxwriter
import numpy as np
from stock import Stock
import util
import condition
from trade_result import TradeResult
from backtest_common import *

# 매매 시간 확인
def isTradeTime(time):
    return 900 <= time <= 1530


# 이동 평균 매매
def backtestMal(cond):
    stockItemList = loadPriceDate(cond.targetStock[0].code)
    groupByDate = getGroupByDate(stockItemList)
    ohlcList = []
    tradeHistory = []

    currentDate = None
    beforeOhlc = None

    beforeTrade = TradeResult(cash=cond.cash)
    currentTrade = None
    todaySkip = False

    for candle in stockItemList:

        # 날짜가 변경 시 초기화 작업
        if currentDate != candle["date"]:
            if currentDate is not None:
                # 현재 날짜 OHLC 계산
                beforeOhlc = getOhlc(groupByDate[currentDate])
                ohlcList.append(beforeOhlc)

                if currentTrade is not None:
                    beforeTrade = currentTrade
                    if not (currentDate < cond.fromDate or currentDate > cond.toDate):
                        tradeHistory.append(currentTrade)
                currentTrade = TradeResult()
                currentTrade.cash = beforeTrade.getFinalResult()
                currentTrade.beforeClose = beforeOhlc["close"]
                currentTrade.candle = candle

            currentDate = candle["date"]
            todaySkip = False

        # 백테스팅 대상 범위가 아니면 skip
        isTestRange = currentDate < cond.fromDate or currentDate > cond.toDate

        if isTestRange:
            continue

        if not isTradeTime(candle["time"]):
            continue

        # 이평선을 계산하기 위한 데이터가 부족하면 매매 하지 않음
        if len(ohlcList) + 1 < cond.longMalDuration:
            continue

        # 매매 가능시간 체크
        if not isTradeTime(candle["time"]):
            continue

        # 오늘 매매가 이루어 졌다면 오늘은 더이상 매매를 하지 않음
        if todaySkip:
            continue

        currentTrade.shortMal = getMalCrrent(ohlcList, cond.shortMalDuration, candle)
        currentTrade.longMal = getMalCrrent(ohlcList, cond.longMalDuration, candle)
        currentTrade.candle = getOhlc(groupByDate[currentDate])

        # 매도 체크
        # TODO

        breakThroughYesterday = isMalUpBeforeDay(cond, ohlcList)
        # 비교 전날 기준 정배열 이동평균을 돌파하였다면 매수 하지 않음
        if breakThroughYesterday:
            continue

        breakThroughCourrent = isMalUp(
            cond.riseBuyRate, currentTrade.shortMal, currentTrade.longMal
        )

        if not breakThroughCourrent:
            continue

        # 매수
        currentTrade.buyPrice = candle["close"] + cond.tradeMargin

        # 매수 가능 금액
        possible = int(beforeTrade.getFinalResult() * cond.investRatio)
        # 매수 가능 수량
        currentTrade.volume = possible // currentTrade.buyPrice

        currentTrade.feePrice = currentTrade.getBuyAmount() * cond.feeBuy
        currentTrade.cash = beforeTrade.getFinalResult() - currentTrade.getBuyAmount()
        todaySkip = True

        print(
            "매수 {}:{}, 단기이평선({}): {:,}, 장기이평선({}): {:,}, 단가:{:,}, 수량:{:,}, 총금액: {:,} ".format(
                candle["date"],
                candle["time"],
                cond.shortMalDuration,
                currentTrade.shortMal,
                cond.longMalDuration,
                currentTrade.longMal,
                currentTrade.buyPrice,
                currentTrade.volume,
                currentTrade.getBuyAmount(),
            )
        )

        currentTrade.isTrade = True

    return tradeHistory


# 현시점 이동평균 가격
def getMalCrrent(ohlcList, duration, currentCandle):
    substract = ohlcList[-(duration - 1) :]
    substract.append(currentCandle)
    closeList = [v["close"] for v in substract]
    return round(np.average(closeList))


# 비교 전날 이동 평균을 돌파했는지 여부 판단
def isMalUpBeforeDay(cond, ohlcList):
    # 전날 이동 평균값 구하기
    substract = ohlcList[-(cond.shortMalDuration) :]
    closeList = [v["close"] for v in substract]
    shortMal = round(np.average(closeList))

    substract = ohlcList[-(cond.longMalDuration) :]
    closeList = [v["close"] for v in substract]
    longMal = round(np.average(closeList))

    return isMalUp(cond.riseBuyRate, shortMal, longMal)


# 정배열 상태에서 이동평균 돌파 판단값
def isMalUp(riseBuyRate, shortMal, longMal):
    compareShortMal = round(shortMal - shortMal * riseBuyRate)
    breakThrough = compareShortMal >= longMal
    return breakThrough


# 역배열 상태에서 이동평균 하락 돌파
def isMalDown(failBuyRate, shortMal, longMal):
    compareShortMal = round(shortMal + shortMal * failBuyRate)
    breakThrough = compareShortMal <= longMal
    return breakThrough


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

    print(
        "{} - 주식수익률: {:.2f}%, 주식MDD: {:.2f}%, 투자수익률: {:.2f}%, 투자MDD: {:.2f}%".format(
            cond.comment,
            result["stockYield"] * 100,
            result["stockMdd"] * 100,
            result["realYield"] * 100,
            result["realMdd"] * 100,
        )
    )
    return result


# 백테스팅 결과 엑셀 파일 만들기
def makeExcel(tradeHistory, cond, analysisResult):
    codes = [item.code for item in cond.targetStock]

    workbook = xlsxwriter.Workbook(
        "backtest_result/{}_{}({}).xlsx".format(
            cond.fromDate, cond.toDate, ",".join(codes)
        )
    )
    worksheet = workbook.add_worksheet("result")
    worksheet.freeze_panes(1, 0)
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

    style2 = workbook.add_format({"num_format": "0.000%", "border": 1})
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
        worksheet.write(idx, 10, trade.buyPrice)
        worksheet.write(idx, 11, trade.isTrailing)
        worksheet.write(idx, 12, trade.volume)
        worksheet.write(idx, 13, trade.highYield)
        worksheet.write(idx, 14, trade.sellPrice)

        # 단기, 장기 이동평균

        worksheet.write(idx, 16, trade.getRealYield())
        worksheet.write(idx, 17, trade.getBuyAmount())
        worksheet.write(idx, 18, trade.cash)
        worksheet.write(idx, 19, trade.getGains())
        worksheet.write(idx, 20, trade.feePrice)
        worksheet.write(idx, 21, trade.getInvestResult())
        worksheet.write(idx, 22, trade.getFinalResult())

    # 투자 요약결과
    baseRowIdx = len(tradeHistory) + 5
    worksheet.write(baseRowIdx, 0, "--------------")
    worksheet.write(baseRowIdx + 1, 0, "실제수익")
    worksheet.write(baseRowIdx + 1, 1, analysisResult["stockYield"], style2)
    worksheet.write(baseRowIdx + 2, 0, "실제MDD")
    worksheet.write(baseRowIdx + 2, 1, analysisResult["stockMdd"], style2)
    worksheet.write(baseRowIdx + 3, 0, "투자수익")
    worksheet.write(baseRowIdx + 3, 1, analysisResult["realYield"], style2)
    worksheet.write(baseRowIdx + 4, 0, "투자MDD")
    worksheet.write(baseRowIdx + 4, 1, analysisResult["realMdd"], style2)

    # 투자 조건
    baseRowIdx = len(tradeHistory) + 12
    worksheet.write(baseRowIdx, 0, "--------------")
    worksheet.write(baseRowIdx + 1, 0, "분석기간")
    worksheet.write(baseRowIdx + 1, 1, cond.getRange())
    worksheet.write(baseRowIdx + 2, 0, "대상종목")
    worksheet.write(baseRowIdx + 2, 1, cond.targetStock[0].getFullName())
    worksheet.write(baseRowIdx + 3, 0, "변동성 비율(K)")
    worksheet.write(baseRowIdx + 3, 1, cond.k, style2)
    worksheet.write(baseRowIdx + 4, 0, "투자비율")
    worksheet.write(baseRowIdx + 4, 1, cond.investRatio, style2)
    worksheet.write(baseRowIdx + 5, 0, "최초 투자금액")
    worksheet.write(baseRowIdx + 5, 1, cond.cash, style1)
    worksheet.write(baseRowIdx + 6, 0, "매매 마진")
    worksheet.write(baseRowIdx + 6, 1, cond.tradeMargin, style1)
    worksheet.write(baseRowIdx + 7, 0, "매수 수수료")
    worksheet.write(baseRowIdx + 7, 1, cond.feeBuy, style2)
    worksheet.write(baseRowIdx + 8, 0, "매도 수수료")
    worksheet.write(baseRowIdx + 8, 1, cond.feeSell, style2)
    worksheet.write(baseRowIdx + 9, 0, "손절률")
    worksheet.write(baseRowIdx + 9, 1, cond.loseStopRate, style2)
    worksheet.write(baseRowIdx + 10, 0, "트레일링스탑 진입률")
    worksheet.write(baseRowIdx + 10, 1, cond.gainStopRate, style2)
    worksheet.write(baseRowIdx + 11, 0, "트레일링스탑 매도률")
    worksheet.write(baseRowIdx + 11, 1, cond.trailingStopRate, style2)
    worksheet.write(baseRowIdx + 12, 0, "조건 설명")
    worksheet.write(baseRowIdx + 12, 1, cond.comment)

    workbook.close()


def makeAnalysisExcel(analysis):
    workbook = xlsxwriter.Workbook("backtest_result/백테스팅결과.xlsx")
    worksheet = workbook.add_worksheet("result")
    worksheet.freeze_panes(1, 0)
    style1 = workbook.add_format({"num_format": "#,###", "border": 1})
    style2 = workbook.add_format({"num_format": "0.000%", "border": 1})
    style3 = workbook.add_format({"border": 1})

    header = [
        "분석기간",
        "대상종목",
        "변동성 비율(K)",
        "투자비율",
        "최초 투자금액",
        "매매 마진",
        "매수 수수료",
        "매도 수수료",
        "손절률",
        "트레일링스탑 진입률",
        "트레일링스탑 매도률",
        "조건 설명",
        "실제수익",
        "실제MDD",
        "투자수익",
        "투자MDD",
    ]
    worksheet.set_row(
        0, None, workbook.add_format({"bold": True, "align": "center", "border": 1})
    )
    for idx, name in enumerate(header):
        worksheet.write(0, idx, name)

    for idx, r in enumerate(analysis, 1):
        cond = r["condition"]
        analysisResult = r["analysisResult"]
        worksheet.write(idx, 0, cond.getRange(), style3)
        worksheet.write(idx, 1, cond.targetStock[0].getFullName(), style2)
        worksheet.write(idx, 2, cond.k, style2)
        worksheet.write(idx, 3, cond.investRatio, style2)
        worksheet.write(idx, 4, cond.cash, style1)
        worksheet.write(idx, 5, cond.tradeMargin, style1)
        worksheet.write(idx, 6, cond.feeBuy, style2)
        worksheet.write(idx, 7, cond.feeSell, style2)
        worksheet.write(idx, 8, cond.loseStopRate, style2)
        worksheet.write(idx, 9, cond.gainStopRate, style2)
        worksheet.write(idx, 10, cond.trailingStopRate, style2)
        worksheet.write(idx, 11, cond.comment, style3)
        worksheet.write(idx, 12, analysisResult["stockYield"], style2)
        worksheet.write(idx, 13, analysisResult["stockMdd"], style2)
        worksheet.write(idx, 14, analysisResult["realYield"], style2)
        worksheet.write(idx, 15, analysisResult["realMdd"], style2)

    workbook.close()
