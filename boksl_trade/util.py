# 수익률 계산
def getYield(values):
    result = (values[len(values) - 1] / values[0]) - 1
    return result


# MDD 계산
def getMdd(values):
    highValue = 0
    mdd = 0
    for v in values:
        if highValue < v:
            highValue = v
        else:
            mdd = min(mdd, v / highValue - 1)
    return mdd
