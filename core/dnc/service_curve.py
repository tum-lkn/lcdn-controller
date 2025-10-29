from __future__ import annotations
from dataclasses import dataclass

import matplotlib.pyplot as plt
import numpy as np

from NetworkCalculus.arrival_curve import ArrivalCurve
import math


@dataclass
class ServiceCurve:
    """
    Represents a *Rate–Latency Service Curve* β(t) = R * max(0, t - T)
    """

    def __init__(self, latency: float, rate: float):
        """
        Init
        """
        self.latency = latency
        self.rate = rate

    def __add__(self, other):
        """
        Concatenate two service curves (in series).

        When two systems are connected in series, their effective
        latency adds up, and the bottleneck rate is the *minimum* of both.

        Args:
            other (ServiceCurve): the service curve to add.

        Returns:
            ServiceCurve: Combined (concatenated) service curve.
        """
        return ServiceCurve(self.latency + other.latency, min(self.rate, other.rate))

    def __str__(self):
        """Return a human-readable string representation of the curve."""
        return f'SC: {self.latency:.9f}s {self.rate:.2f} bps'

    def conv(self, ac: ArrivalCurve) -> ArrivalCurve:
        """
        Perform convolution of the service curve with an arrival curve.

        This computes the output arrival curve α' = α ⊗ β.
        If the flow's rate exceeds the service rate, the system
        becomes unstable, returning an infinite arrival curve.

        Args:
            ac (ArrivalCurve): The incoming arrival curve.

        Returns:
            ArrivalCurve: The resulting arrival curve after service.
        """
        if ac.rate > self.rate:
            return ArrivalCurve(rate=math.inf, burst=math.inf)
        else:
            return ArrivalCurve(rate=ac.rate, burst=ac.burst + ac.rate * self.latency)

    def conv_threshold(self, ac: ArrivalCurve, threshold: float) -> ArrivalCurve:
        """
        Variant of convolution with Queue Level Thresholds.

        Args:
            ac (ArrivalCurve): Input arrival curve.
            threshold (float): Queue-specific threshold delay.

        Returns:
            ArrivalCurve: The resulting arrival curve after service.
        """
        if ac.rate > self.rate:
            return ArrivalCurve(rate=math.inf, burst=math.inf)
        else:
            return ArrivalCurve(rate=ac.rate, burst=ac.burst + ac.rate * threshold)

    def delay(self, ac: ArrivalCurve) -> float:
        """
        Compute worst-case delay bound for a given arrival curve.

        D = (b + R*T) / R, where b is burst, R is rate, and T is latency.

        Args:
            ac (ArrivalCurve): Arrival curve.

        Returns:
            float: Delay bound (seconds), or inf if unstable.
        """
        if ac.rate > self.rate:
            return math.inf
        else:
            return (ac.burst + self.latency * self.rate) / self.rate

    def buffer(self, ac: ArrivalCurve) -> float:
        """
        Compute the required buffer size for the flow.

        Args:
            ac (ArrivalCurve): Arrival curve.

        Returns:
            float: Required buffer (bits), or inf if unstable.
        """
        if ac.rate > self.rate:
            return math.inf
        else:
            return ac.burst + ac.rate * self.latency

    def buffer_threshold(self, ac: ArrivalCurve, threshold: float) -> float:
        """
        Compute buffer requirement with the queue threshold.

        Args:
            ac (ArrivalCurve): Arrival curve.
            threshold (float):  Threshold (seconds).

        Returns:
            float: Required buffer (bits), or inf if unstable.
        """
        if ac.rate > self.rate:
            return math.inf
        else:
            return ac.burst + ac.rate * threshold

    def residual(self, ac: ArrivalCurve) -> ServiceCurve:
        """
        Compute the *residual service curve* after serving a given flow.

        β'(t) = (R - r) * (t - T'), where:
            - r: arrival rate of the flow
            - T' = (b + R*T) / (R - r)

        Args:
            ac (ArrivalCurve): The flow's arrival curve.

        Returns:
            ServiceCurve: The residual service curve available to others.
        """
        if ac.rate > self.rate:
            return ServiceCurve(0.0, 0.0)
        else:
            return ServiceCurve(rate=self.rate - ac.rate,
                                latency=(ac.burst + self.rate * self.latency) / (self.rate - ac.rate))