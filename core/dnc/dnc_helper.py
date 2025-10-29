import matplotlib.pyplot as plt
import numpy as np
import math

from core.dnc.arrival_curve import ArrivalCurve
from core.dnc.service_curve import ServiceCurve


def plot_dnc_curves(sc: ServiceCurve, ac: ArrivalCurve):
    """
    Plots the arrival curve and the service curve of a link.

    Only really useful for debugging and testing.

    Args:
        sc (ServiceCurve): the service curve of the link.
        ac (ArrivalCurve): the arrival curve of the link.
    """
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