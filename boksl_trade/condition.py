# 매매 조건
class Condition:
    def __init__(
        self,
        targetStock,
        investRatio,
        fromDate,
        toDate,
        cash,
        tradeMargin,
        feeBuy,
        feeSell,
        downSellRate,
        upBuyRate,
        shortMalDuration,
        longMalDuration,
        comment,
    ):
        self.__targetStock = targetStock  # 대상종목
        self.__investRatio = investRatio  # 총 현금을 기준으로 투자 비율. 1은 전액, 0.5은 50% 투자
        self.__fromDate = fromDate  # 분석대상 기간 - 시작
        self.__toDate = toDate  # 분석대상 기간 - 종료
        self.__cash = cash  # 최초 투자금액
        self.__tradeMargin = tradeMargin  # 매매시 채결 가격 차이
        self.__feeBuy = feeBuy  # 매수 수수료
        self.__feeSell = feeSell  # 매도 수수료
        self.__downSellRate = downSellRate  # 하락 매도률
        self.__upBuyRate = upBuyRate  # 상승 매수률
        self.__shortMalDuration = shortMalDuration  # 짧은 이동평균 기간
        self.__longMalDuration = longMalDuration  # 기간 이동평균 기간
        self.__comment = comment  # 조건에대한 설명글

    @property
    def targetStock(self):
        return self.__targetStock

    @property
    def investRatio(self):
        return self.__investRatio

    @property
    def fromDate(self):
        return self.__fromDate

    @property
    def toDate(self):
        return self.__toDate

    @property
    def cash(self):
        return self.__cash

    @property
    def tradeMargin(self):
        return self.__tradeMargin

    @property
    def feeBuy(self):
        return self.__feeBuy

    @property
    def feeSell(self):
        return self.__feeSell

    @property
    def downSellRate(self):
        return self.__downSellRate

    @property
    def upBuyRate(self):
        return self.__upBuyRate

    @property
    def shortMalDuration(self):
        return self.__shortMalDuration

    @property
    def longMalDuration(self):
        return self.__longMalDuration

    @property
    def comment(self):
        return self.__comment

    def getRange(self):
        return str(self.__fromDate) + " ~ " + str(self.__toDate)
