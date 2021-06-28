class TradeResult:
    def __init__(
        self,
        candle={},
        buyPrice=0,
        sellPrice=0,
        volume=0,
        cash=0,
        feePrice=0,
        beforeClose=0,
        shortMal=0,
        longMal=0,
    ):
        self.__candle = candle  # 매수 시점 캔들
        self.__buyPrice = buyPrice  # 매수 체결 가격
        self.__sellPrice = sellPrice  # 매도 체결 가격
        self.__volume = volume  # 주식 수량
        self.__cash = cash  # 현금
        self.__feePrice = feePrice  # 매매 수수료
        self.__beforeClose = beforeClose  # 직전 캔들 종가
        self.__shortMal = shortMal  # 단기 이평선 가격
        self.__longMal = longMal  # 장기 이평선 가격

    @property
    def candle(self):
        return self.__candle

    @candle.setter
    def candle(self, value):
        self.__candle = value

    @property
    def buyPrice(self):
        return self.__buyPrice

    @buyPrice.setter
    def buyPrice(self, value):
        self.__buyPrice = value

    @property
    def sellPrice(self):
        return self.__sellPrice

    @sellPrice.setter
    def sellPrice(self, value):
        self.__sellPrice = value

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
    def beforeClose(self):
        return self.__beforeClose

    @beforeClose.setter
    def beforeClose(self, value):
        self.__beforeClose = value

    @property
    def shortMal(self):
        return self.__shortMal

    @shortMal.setter
    def shortMal(self, value):
        self.__shortMal = value

    @property
    def longMal(self):
        return self.__longMal

    @longMal.setter
    def longMal(self, value):
        self.__longMal = value

    def isBuy(self):
        return self.buyPrice != 0

    def isSell(self):
        return self.sellPrice != 0

    # 매수금액
    def getBuyAmount(self):
        return self.volume * self.buyPrice

    # 매도금액
    def getSellAmount(self):
        return self.volume * self.sellPrice

    # 실현 수익
    def getRealYield(self):
        # 매도 상태
        if self.isSell():
            return (self.sellPrice / self.buyPrice) - 1
        # 매수 상태
        elif self.isBuy():
            return (self.candle["close"] / self.buyPrice) - 1
        return 0

    # 투자 수익
    def getGains(self):
        return self.getBuyAmount() * self.getRealYield()

    # 투자금 + 투자 수익 = 투자 결과
    def getInvestResult(self):
        return self.getBuyAmount() + self.getGains()

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
            + "종가: {close:,}, 직전 종가: {beforeClose:,}, 단기 이동평균: {shortMal:,}, 장기 이동평균: {longMal:,}, "
            + "당일 수익률: {candleYield:0,.2f}%, 장중 수익률: {marketYield:0,.2f}%, 매수 여부: {isBuy}, "
            + "매수 체결 가격: {buyPrice:,}, 매수 수량: {volume:,}, 매도 체결 가격: {sellPrice:,}, "
            + "실현 수익률: {realYield:,.2f}%, 투자금: {investmentAmount:,}, 현금: {cash:,.0f}, 투자 수익: {gains:,.0f}, 수수료: {feePrice:,.0f}, "
            + "투자 결과: {investResult:,.0f}, 현금+투자결과-수수료: {finalResult:,.0f}"
        ).format(
            date=self.candle["date"],
            open=self.candle["open"],
            high=self.candle["high"],
            low=self.candle["low"],
            close=self.candle["close"],
            beforeClose=self.beforeClose,
            shortMal=self.shortMal,
            longMal=self.longMal,
            candleYield=self.getCandleYield() * 100,
            marketYield=self.getMarketYield() * 100,
            isBuy=self.isBuy(),
            buyPrice=self.buyPrice,
            volume=self.volume,
            sellPrice=self.sellPrice,
            realYield=self.getRealYield() * 100,
            investmentAmount=self.getBuyAmount(),
            cash=self.cash,
            gains=self.getGains(),
            feePrice=self.feePrice,
            investResult=self.getInvestResult(),
            finalResult=self.getFinalResult(),
        )
