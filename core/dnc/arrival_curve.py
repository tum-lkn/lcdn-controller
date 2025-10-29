class ArrivalCurve:
    """
    Represents a *Token Bucket Arrival Curve* used in Network Calculus.

    The token bucket model describes traffic shaping or flow control
    where data is constrained by two parameters:

    - **rate (r)**: the sustained rate (bits per second)
    - **burst (b)**: the maximum deviation at time t from r (bits)

    The arrival curve α(t) = r * t + b defines the maximum
    amount of data that can arrive in any time interval t.
    """

    def __init__(self, rate: float = 0.0, burst: float = 0.0): 
        """
        Initialize a new ArrivalCurve instance.

        Args:
            rate (float): Sustained arrival rate (bits per second).
            burst (float): Burst size (bits).
        """
        self.rate = max(rate, 0.0)
        self.burst = max(burst, 0.0)

    def __add__(self, other):
        """
        Combine two arrival curves.

        Args:
            other (ArrivalCurve): The other arrival curve to add.

        Returns:
            ArrivalCurve: New curve representing the combined traffic.
        """
        return ArrivalCurve(rate=self.rate + other.rate, burst=self.burst + other.burst)

    def __sub__(self, other):
        """
        Subtract one arrival curve from another (removing a flow).

        Useful when removing a flow reservation.
        Negative results are clipped to zero.

        Args:
            other (ArrivalCurve): The other arrival curve to subtract.

        Returns:
            ArrivalCurve: New curve representing remaining traffic.
        """
        rate = max(self.rate - other.rate, 0.0)
        burst = max(self.burst - other.burst, 0.0)
        return ArrivalCurve(rate=rate, burst=burst)

    def __str__(self):
        """
        Returns a human-readable representation of the arrival curve.

        Example:
            AC: 10.00 bps, 5.00 bit
        """
        return f'AC: {self.rate:.2f} bps, {self.burst:.2f} bit'
