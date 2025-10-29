# test_service_curve.py
import math
import pytest
from NetworkCalculus.arrival_curve import ArrivalCurve
from NetworkCalculus.service_curve import ServiceCurve


class TestServiceCurve:
    def test_initialization_and_str(self):
        sc = ServiceCurve(latency=0.1, rate=100.0)
        assert sc.latency == 0.1
        assert sc.rate == 100.0
        assert "SC:" in str(sc)

    def test_addition_of_two_service_curves(self):
        sc1 = ServiceCurve(latency=0.1, rate=100.0)
        sc2 = ServiceCurve(latency=0.2, rate=80.0)
        result = sc1 + sc2
        # Latencies add; rate is the minimum
        assert result.latency == pytest.approx(0.3)
        assert result.rate == pytest.approx(80.0)

    def test_conv_with_valid_arrival_curve(self):
        sc = ServiceCurve(latency=0.1, rate=100.0)
        ac = ArrivalCurve(rate=50.0, burst=10.0)
        result = sc.conv(ac)
        # Should preserve rate, burst increased by rate * latency
        assert isinstance(result, ArrivalCurve)
        assert result.rate == 50.0
        assert result.burst == pytest.approx(10.0 + 50.0 * 0.1)

    def test_conv_with_unstable_arrival_curve(self):
        sc = ServiceCurve(latency=0.1, rate=100.0)
        ac = ArrivalCurve(rate=150.0, burst=10.0)
        result = sc.conv(ac)
        assert math.isinf(result.rate)
        assert math.isinf(result.burst)

    def test_delay_calculation(self):
        sc = ServiceCurve(latency=0.1, rate=100.0)
        ac = ArrivalCurve(rate=50.0, burst=10.0)
        expected_delay = (10.0 + 0.1 * 100.0) / 100.0
        assert sc.delay(ac) == pytest.approx(expected_delay)

    def test_delay_unstable_returns_inf(self):
        sc = ServiceCurve(latency=0.1, rate=100.0)
        ac = ArrivalCurve(rate=200.0, burst=10.0)
        assert math.isinf(sc.delay(ac))

    def test_buffer_calculation(self):
        sc = ServiceCurve(latency=0.2, rate=100.0)
        ac = ArrivalCurve(rate=50.0, burst=10.0)
        assert sc.buffer(ac) == pytest.approx(10.0 + 50.0 * 0.2)

    def test_residual_service_curve(self):
        sc = ServiceCurve(latency=0.1, rate=100.0)
        ac = ArrivalCurve(rate=40.0, burst=20.0)
        residual = sc.residual(ac)
        assert isinstance(residual, ServiceCurve)
        assert residual.rate == pytest.approx(60.0)
        expected_latency = (20.0 + 100.0 * 0.1) / 60.0
        assert residual.latency == pytest.approx(expected_latency)

    def test_residual_unstable_returns_zero_curve(self):
        sc = ServiceCurve(latency=0.1, rate=100.0)
        ac = ArrivalCurve(rate=150.0, burst=10.0)
        residual = sc.residual(ac)
        assert residual.rate == 0.0
        assert residual.latency == 0.0
