class Stock:
    def __init__(
        self,
        code,
        name,
        isDerivative,
    ):
        self.__code = code  # 종목 코드
        self.__name = name  # 종목 이름
        self.__isDerivative = isDerivative  # 파생상품 여부

    @property
    def code(self):
        return self.__code

    @property
    def name(self):
        return self.__name

    @property
    def isDerivative(self):
        return self.__isDerivative

    def getFullName(self):
        return self.name + "(" + self.code + ")"
