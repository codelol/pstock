class Metrics:
    """
    calculate exponential moving average
    datapoints[0] is the most recent price
    """
    def ema(self, datapoints, days) :
        ratio = float(2 / (days + 1))
        cur_ema = 0
        emas = []
        for i in reversed(range(len(datapoints))):
            cur_ema = datapoints[i] * ratio + cur_ema * (1 - ratio)
            emas.insert(0, cur_ema)
        return emas