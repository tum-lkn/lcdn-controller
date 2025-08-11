class ArrivalCurve:
    """
    Class for representing an Token Bucket Arrival Curve
    """

    def __init__(self, rate: float = 0.0, burst: float = 0.0): 
        """
        :param rate: rate of the token bucket arrival curve
        :param burst: burst of the token bucket arrival curve
        """
        self.rate = max(rate, 0.0)
        self.burst = max(burst, 0.0)

    def __add__(self, other):
        return ArrivalCurve(rate=self.rate + other.rate, burst=self.burst + other.burst)

    def __sub__(self, other):
        rate = max(self.rate - other.rate, 0.0)
        burst = max(self.burst - other.burst, 0.0)
        return ArrivalCurve(rate=rate, burst=burst)

    def __str__(self):
        return f'AC: {self.rate:.2f} bps, {self.burst:.2f} bit'


if __name__ == '__main__':
    ac1 = ArrivalCurve(rate=1.0, burst=2.0)
    ac2 = ArrivalCurve(rate=2.0, burst=3.0)

    print(ac1 - ac2)
