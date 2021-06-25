from enum import Enum, auto

# 매도 유형
class AskReason(Enum):
    TIME = auto()  # 매도 시간 경과
    LOSS = auto()  # 손절 매도
    GAIN = auto()  # 익절 매도


# 매매 결과
class TradeResult:
    def __init__(
        self,
        candle={},
        targetPrice=0,
        isTrade=False,
        bidPrice=0,
        askPrice=0,
        volume=0,
        cash=0,
        feePrice=0,
        highYield=0,
        askReason=None,
        beforeClose=0,
        isTrailing=False,
    ):
        self.__candle = candle  # 매수 시점 캔들
        self.__targetPrice = targetPrice  # 매매주기 목표가
        self.__isTrade = isTrade  # 매매 여부
        self.__bidPrice = bidPrice  # 매수 체결 가격
        self.__askPrice = askPrice  # 매도 체결 가격
        self.__volume = volume  # 주식 수량
        self.__cash = cash  # 현금
        self.__feePrice = feePrice  # 매매 수수료
        self.__highYield = highYield  # 최고 수익률
        self.__askReason = askReason  # 매도 이유
        self.__beforeClose = beforeClose  # 직전 캔들 종가
        self.__isTrailing = isTrailing  # 트레일링 스탑 진입 여부

    @property
    def candle(self):
        return self.__candle

    @candle.setter
    def candle(self, value):
        self.__candle = value

    @property
    def targetPrice(self):
        return self.__targetPrice

    @targetPrice.setter
    def targetPrice(self, value):
        self.__targetPrice = value

    @property
    def isTrade(self):
        return self.__isTrade

    @isTrade.setter
    def isTrade(self, value):
        self.__isTrade = value

    @property
    def isTrailing(self):
        return self.__isTrailing

    @isTrailing.setter
    def isTrailing(self, value):
        self.__isTrailing = value

    @property
    def bidPrice(self):
        return self.__bidPrice

    @bidPrice.setter
    def bidPrice(self, value):
        self.__bidPrice = value

    @property
    def askPrice(self):
        return self.__askPrice

    @askPrice.setter
    def askPrice(self, value):
        self.__askPrice = value

    @property
    def volume(self):
        return self.__volume

    @volume.setter
    def volume(self, value):
        self.__volume = value

    @property
    def cash(self):
        return self.__cash

    @cash.setter
    def cash(self, value):
        self.__cash = value

    @property
    def feePrice(self):
        return self.__feePrice

    @feePrice.setter
    def feePrice(self, value):
        self.__feePrice = value

    @property
    def highYield(self):
        return self.__highYield

    @highYield.setter
    def highYield(self, value):
        self.__highYield = value

    @property
    def askReason(self):
        return self.__askReason

    @askReason.setter
    def askReason(self, value):
        self.__askReason = value

    @property
    def beforeClose(self):
        return self.__beforeClose

    @beforeClose.setter
    def beforeClose(self, value):
        self.__beforeClose = value

    # 매수금액
    def getBidAmount(self):
        return self.volume * self.bidPrice

    # 매도금액
    def getAskAmount(self):
        return self.volume * self.askPrice

    # 실현 수익
    def getRealYield(self):
        if self.isTrade:
            return (self.askPrice / self.bidPrice) - 1
        return 0

    # 투자 수익
    def getGains(self):
        return self.getBidAmount() * self.getRealYield()

    # 투자금 + 투자 수익 = 투자 결과
    def getInvestResult(self):
        return self.getBidAmount() + self.getGains()

    # 현금 + 투자 결과
    # 투자금 + 투자 수익 - 수수료
    def getFinalResult(self):
        return self.getInvestResult() + self.cash - self.feePrice

    # 직전 캔들 종가에 매수 해서 종가에 매도 했을 때 얻는 수익률
    def getCandleYield(self):
        diff = self.candle["close"] - self.beforeClose
        return diff / self.beforeClose

    # 장중 수익률
    def getMarketYield(self):
        diff = self.candle["close"] - self.candle["open"]
        return diff / self.candle["open"]

    def toString(self):
        return (
            "날짜: {date}, 시가: {open:,}, 고가:{high:,}, 저가: {low:,}, "
            + "종가: {close:,}, 직전 종가: {beforeClose:,}, 당일 수익률: {candleYield:0,.2f}%, 장중 수익률: {marketYield:0,.2f}%, 매수 목표가: {targetPrice:,}, 매매여부: {isTrade}, "
            + "매수 체결 가격: {bidPrice:,}, 트레일링 스탑 진입 여부: {isTrailing}, 매수 수량: {volume:,}, "
            + "최고수익률: {highYield:0,.2f}%, 매도 체결 가격: {askPrice:,}, 매도 이유: {askReason}, "
            + "실현 수익률: {realYield:,.2f}%, 투자금: {investmentAmount:,}, 현금: {cash:,.0f}, 투자 수익: {gains:,.0f}, 수수료: {feePrice:,.0f}, "
            + "투자 결과: {investResult:,.0f}, 현금+투자결과-수수료: {finalResult:,.0f}"
        ).format(
            date=self.candle["date"],
            open=self.candle["open"],
            high=self.candle["high"],
            low=self.candle["low"],
            close=self.candle["close"],
            beforeClose=self.beforeClose,
            candleYield=self.getCandleYield() * 100,
            marketYield=self.getMarketYield() * 100,
            targetPrice=self.targetPrice,
            isTrade=self.isTrade,
            bidPrice=self.bidPrice,
            isTrailing=self.isTrailing,
            volume=self.volume,
            highYield=self.highYield * 100,
            askPrice=self.askPrice,
            askReason=self.askReason.name if self.askReason is not None else "-",
            realYield=self.getRealYield() * 100,
            investmentAmount=self.getBidAmount(),
            cash=self.cash,
            gains=self.getGains(),
            feePrice=self.feePrice,
            investResult=self.getInvestResult(),
            finalResult=self.getFinalResult(),
        )
