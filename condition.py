# 매매 조건
class Condition:
    def __init__(
        self,
        k,
        investRatio,
        fromDate,
        toDate,
        cash,
        tradeMargin,
        feeBid,
        feeAsk,
        loseStopRate,
        gainStopRate,
    ):
        self.__k = k  #  변동성 돌파 판단 비율
        self.__investRatio = investRatio  # 총 현금을 기준으로 투자 비율. 1은 전액, 0.5은 50% 투자
        self.__fromDate = fromDate  # 분석대상 기간 - 시작
        self.__toDate = toDate  # 분석대상 기간 - 종료
        self.__cash = cash  # 최초 투자금액
        self.__tradeMargin = tradeMargin  # 매매시 채결 가격 차이
        self.__feeBid = feeBid  # 매수 수수료
        self.__feeAsk = feeAsk  # 매도 수수료
        self.__loseStopRate = loseStopRate  # 손절라인
        self.__gainStopRate = gainStopRate  # 익절라인

    @property
    def k(self):
        return self.__k

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
    def feeBid(self):
        return self.__feeBid

    @property
    def feeAsk(self):
        return self.__feeAsk

    @property
    def loseStopRate(self):
        return self.__loseStopRate

    @property
    def gainStopRate(self):
        return self.__gainStopRate
