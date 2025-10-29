from NetworkCalculus.arrival_curve import ArrivalCurve


class TestArrivalCurve:
    def test_initialization_defaults(self):
        ac = ArrivalCurve()
        assert ac.rate == 0.0
        assert ac.burst == 0.0

    def test_initialization_positive_values(self):
        ac = ArrivalCurve(rate=10.5, burst=5.2)
        assert ac.rate == 10.5
        assert ac.burst == 5.2

    def test_initialization_negative_values_clamped(self):
        ac = ArrivalCurve(rate=-10, burst=-3)
        assert ac.rate == 0.0
        assert ac.burst == 0.0

    def test_addition_of_two_curves(self):
        ac1 = ArrivalCurve(rate=10, burst=5)
        ac2 = ArrivalCurve(rate=2, burst=1)
        result = ac1 + ac2
        assert isinstance(result, ArrivalCurve)
        assert result.rate == 12
        assert result.burst == 6

    def test_subtraction_of_two_curves(self):
        ac1 = ArrivalCurve(rate=10, burst=5)
        ac2 = ArrivalCurve(rate=3, burst=2)
        result = ac1 - ac2
        assert result.rate == 7
        assert result.burst == 3

    def test_subtraction_clamps_to_zero(self):
        ac1 = ArrivalCurve(rate=5, burst=1)
        ac2 = ArrivalCurve(rate=10, burst=3)
        result = ac1 - ac2
        assert result.rate == 0.0
        assert result.burst == 0.0

    def test_str_representation(self):
        ac = ArrivalCurve(rate=10, burst=5)
        s = str(ac)
        assert "AC:" in s
        assert "10.00" in s
        assert "5.00" in s
