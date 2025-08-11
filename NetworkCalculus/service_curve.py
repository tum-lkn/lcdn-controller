from __future__ import annotations
from dataclasses import dataclass

import matplotlib.pyplot as plt
import numpy as np

from NetworkCalculus.arrival_curve import ArrivalCurve
import math

def plot_dnc_curves(sc: ServiceCurve, ac: ArrivalCurve):
    # Find the intersection of both curves
    t_sc = -1 * sc.rate * sc.latency
    intersection_x = (ac.burst - t_sc) / (sc.rate - ac.rate)
    intersection_y = math.ceil(ac.rate * intersection_x + ac.burst)
    upper_y = 2 * intersection_y
    upper_x = 2 * intersection_x

    plt.vlines(0.0, ymin=0.0, ymax=ac.burst, color='red', linewidths=5)
    plt.hlines(0.0, xmin=0.0, xmax=sc.latency, color='blue', linewidths=5)

    ac_x = np.linspace(0, upper_x, 100)
    sc_x = np.linspace(0, upper_x, 100)
    ac_y = ac.burst + ac.rate * ac_x

    sc_y = t_sc + sc.rate * sc_x

    plt.plot(ac_x, ac_y, color='red', linewidth=2)
    plt.plot(sc_x, sc_y, color='blue', linewidth=2)

    plt.ylim([0.0, upper_y])
    plt.xlim([0.0, upper_x])

    plt.show()


@dataclass
class ServiceCurve:
    latency: float
    rate: float

    def __add__(self, other):
        return ServiceCurve(self.latency + other.latency, min(self.rate, other.rate))

    def __str__(self):
        return f'SC: {self.latency:.9f}s {self.rate:.2f} bps'

    def conv(self, ac: ArrivalCurve) -> ArrivalCurve:
        if ac.rate > self.rate:
            return ArrivalCurve(rate=math.inf, burst=math.inf)
        else:
            return ArrivalCurve(rate=ac.rate, burst=ac.burst + ac.rate * self.latency)

    def conv_chameleon(self, ac: ArrivalCurve, threshold: float) -> ArrivalCurve:
        if ac.rate > self.rate:
            return ArrivalCurve(rate=math.inf, burst=math.inf)
        else:
            return ArrivalCurve(rate=ac.rate, burst=ac.burst + ac.rate * threshold)

    def delay(self, ac: ArrivalCurve) -> float:
        if ac.rate > self.rate:
            return math.inf
        else:
            return (ac.burst + self.latency * self.rate) / self.rate

    def buffer(self, ac: ArrivalCurve) -> float:
        if ac.rate > self.rate:
            return math.inf
        else:
            return ac.burst + ac.rate * self.latency

    def buffer_chameleon(self, ac: ArrivalCurve, threshold: float) -> float:
        if ac.rate > self.rate:
            return math.inf
        else:
            return ac.burst + ac.rate * threshold

    def residual(self, ac: ArrivalCurve) -> ServiceCurve:
        if ac.rate > self.rate:
            return ServiceCurve(0.0, 0.0)
        else:
            return ServiceCurve(rate=self.rate - ac.rate,
                                latency=(ac.burst + self.rate * self.latency) / (self.rate - ac.rate))


if __name__ == '__main__':
    ac1 = ArrivalCurve(2.0, 5.0)
    sc1 = ServiceCurve(2.0, 10.0)
    plot_dnc_curves(sc1, ac1)