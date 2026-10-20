"""
Unit Tests for Supply Chain Module (EOQ Calculations)

This test suite validates the correctness of all EOQ calculation functions
against known formula results and edge cases.

Run from the PROJECT ROOT with:
    python -m pytest tests/

Test Coverage:
    - Economic Order Quantity (EOQ)
    - Reorder Point (ROP)
    - Safety Stock (SS)
    - Total Annual Cost (TAC)
    - Orders Per Year
"""

import pytest
import math
from models.eoq import (
    calculate_eoq,
    calculate_reorder_point,
    calculate_safety_stock,
    calculate_total_annual_cost,
    orders_per_year
)


class TestEOQ:
    """Test suite for EOQ calculations."""

    def test_calculate_eoq_basic(self):
        """
        Test EOQ calculation with known values.

        Example: Annual demand = 1000, Ordering cost = 50, Holding cost = 5
        Expected EOQ ≈ 141.42 units
        Formula: √(2 × 1000 × 50 / 5) = √20000 ≈ 141.42
        """
        result = calculate_eoq(1000, 50, 5)
        expected = math.sqrt((2 * 1000 * 50) / 5)
        assert abs(result - expected) < 0.01

    def test_calculate_eoq_edge_case_low_demand(self):
        """Test EOQ with very low annual demand."""
        result = calculate_eoq(100, 50, 5)
        expected = math.sqrt((2 * 100 * 50) / 5)
        assert abs(result - expected) < 0.01
        assert result > 0

    def test_calculate_eoq_edge_case_high_demand(self):
        """Test EOQ with very high annual demand."""
        result = calculate_eoq(100000, 50, 5)
        expected = math.sqrt((2 * 100000 * 50) / 5)
        assert abs(result - expected) < 0.01
        assert result > 0

    def test_calculate_eoq_invalid_holding_cost(self):
        """Test EOQ raises error with zero or negative holding cost."""
        with pytest.raises(ValueError):
            calculate_eoq(1000, 50, 0)

        with pytest.raises(ValueError):
            calculate_eoq(1000, 50, -5)

    def test_calculate_eoq_invalid_ordering_cost(self):
        """Test EOQ with negative ordering cost."""
        with pytest.raises(ValueError):
            calculate_eoq(1000, -50, 5)

    def test_calculate_eoq_invalid_demand(self):
        """Test EOQ with negative demand."""
        with pytest.raises(ValueError):
            calculate_eoq(-1000, 50, 5)


class TestReorderPoint:
    """Test suite for Reorder Point calculations."""

    def test_calculate_reorder_point_basic(self):
        """
        Test Reorder Point calculation with known values.

        Example: Daily demand = 10, Lead time = 5 days, Safety stock = 20
        Expected ROP = (10 × 5) + 20 = 70 units
        """
        result = calculate_reorder_point(10, 5, 20)
        expected = (10 * 5) + 20
        assert result == expected

    def test_calculate_reorder_point_no_safety_stock(self):
        """Test ROP with zero safety stock."""
        result = calculate_reorder_point(10, 5, 0)
        expected = (10 * 5) + 0
        assert result == expected
        assert result == 50

    def test_calculate_reorder_point_long_lead_time(self):
        """Test ROP with long supplier lead time."""
        result = calculate_reorder_point(10, 30, 20)
        expected = (10 * 30) + 20
        assert result == expected
        assert result == 320

    def test_calculate_reorder_point_zero_daily_demand(self):
        """Test ROP with zero daily demand."""
        result = calculate_reorder_point(0, 5, 20)
        assert result == 20

    def test_calculate_reorder_point_invalid_values(self):
        """Test ROP raises error with negative values."""
        with pytest.raises(ValueError):
            calculate_reorder_point(-10, 5, 20)

        with pytest.raises(ValueError):
            calculate_reorder_point(10, -5, 20)

        with pytest.raises(ValueError):
            calculate_reorder_point(10, 5, -20)


class TestSafetyStock:
    """Test suite for Safety Stock calculations."""

    def test_calculate_safety_stock_basic(self):
        """
        Test Safety Stock calculation with known values.

        Example: Z-score = 1.65, Std dev = 5, Lead time = 7 days
        Expected SS = 1.65 × 5 × √7 ≈ 21.8 units
        """
        result = calculate_safety_stock(1.65, 5, 7)
        expected = 1.65 * 5 * math.sqrt(7)
        assert abs(result - expected) < 0.01

    def test_calculate_safety_stock_high_service_level(self):
        """Test Safety Stock with high service level (Z=2.33 for 99%)."""
        result = calculate_safety_stock(2.33, 5, 7)
        expected = 2.33 * 5 * math.sqrt(7)
        assert abs(result - expected) < 0.01
        assert result > calculate_safety_stock(1.65, 5, 7)

    def test_calculate_safety_stock_low_variability(self):
        """Test Safety Stock with low demand variability."""
        result = calculate_safety_stock(1.65, 1, 7)
        expected = 1.65 * 1 * math.sqrt(7)
        assert abs(result - expected) < 0.01
        assert result < calculate_safety_stock(1.65, 5, 7)

    def test_calculate_safety_stock_zero_zscore(self):
        """Test Safety Stock with zero Z-score."""
        result = calculate_safety_stock(0, 5, 7)
        assert result == 0

    def test_calculate_safety_stock_invalid_values(self):
        """Test Safety Stock raises error with negative values."""
        with pytest.raises(ValueError):
            calculate_safety_stock(-1.65, 5, 7)

        with pytest.raises(ValueError):
            calculate_safety_stock(1.65, -5, 7)

        with pytest.raises(ValueError):
            calculate_safety_stock(1.65, 5, -7)


class TestTotalAnnualCost:
    """Test suite for Total Annual Cost calculations."""

    def test_calculate_total_annual_cost_basic(self):
        """
        Test Total Annual Cost calculation with known values.

        Example: Demand = 1000, Order qty = 100, Ordering cost = 50, Holding cost = 5
        Expected TAC = (1000/100 × 50) + (100/2 × 5) = 500 + 250 = 750
        """
        result = calculate_total_annual_cost(1000, 100, 50, 5)
        expected = (1000 / 100 * 50) + (100 / 2 * 5)
        assert abs(result - expected) < 0.01
        assert abs(result - 750) < 0.01

    def test_calculate_total_annual_cost_eoq_optimal(self):
        """
        Test that TAC is minimized at EOQ quantity.

        Verify that total cost at EOQ is lower than at other quantities.
        """
        eoq = calculate_eoq(1000, 50, 5)
        tac_at_eoq = calculate_total_annual_cost(1000, eoq, 50, 5)

        tac_small = calculate_total_annual_cost(1000, 50, 50, 5)
        tac_large = calculate_total_annual_cost(1000, 200, 50, 5)

        assert tac_at_eoq <= tac_small
        assert tac_at_eoq <= tac_large

    def test_calculate_total_annual_cost_small_orders(self):
        """Test TAC with small order quantities (high ordering cost)."""
        result = calculate_total_annual_cost(1000, 50, 50, 5)
        ordering_cost = (1000 / 50) * 50  # = 1000
        holding_cost = (50 / 2) * 5       # = 125
        expected = ordering_cost + holding_cost
        assert abs(result - expected) < 0.01

    def test_calculate_total_annual_cost_large_orders(self):
        """Test TAC with large order quantities (high holding cost)."""
        result = calculate_total_annual_cost(1000, 500, 50, 5)
        ordering_cost = (1000 / 500) * 50  # = 100
        holding_cost = (500 / 2) * 5       # = 1250
        expected = ordering_cost + holding_cost
        assert abs(result - expected) < 0.01

    def test_calculate_total_annual_cost_invalid_order_qty(self):
        """Test TAC raises error with zero or negative order quantity."""
        with pytest.raises(ValueError):
            calculate_total_annual_cost(1000, 0, 50, 5)

        with pytest.raises(ValueError):
            calculate_total_annual_cost(1000, -100, 50, 5)

    def test_calculate_total_annual_cost_invalid_demand(self):
        """Test TAC with negative demand."""
        with pytest.raises(ValueError):
            calculate_total_annual_cost(-1000, 100, 50, 5)


class TestOrdersPerYear:
    """Test suite for Orders Per Year calculations."""

    def test_orders_per_year_basic(self):
        """
        Test orders per year with known values.

        Example: Demand = 1000, Order qty = 100
        Expected = 1000 / 100 = 10 orders per year
        """
        result = orders_per_year(1000, 100)
        assert result == 10

    def test_orders_per_year_with_eoq(self):
        """Test orders per year using the EOQ as the order quantity."""
        eoq = calculate_eoq(1000, 50, 5)
        result = orders_per_year(1000, eoq)
        expected = 1000 / eoq
        assert abs(result - expected) < 0.01
        assert result > 0

    def test_orders_per_year_invalid_order_qty(self):
        """Test orders per year raises error with zero or negative order qty."""
        with pytest.raises(ValueError):
            orders_per_year(1000, 0)

        with pytest.raises(ValueError):
            orders_per_year(1000, -50)

    def test_orders_per_year_invalid_demand(self):
        """Test orders per year with negative demand."""
        with pytest.raises(ValueError):
            orders_per_year(-1000, 100)


class TestIntegration:
    """Integration tests combining multiple functions."""

    def test_complete_inventory_decision(self):
        """
        Test a complete inventory management decision flow.

        Scenario: Given annual demand, costs, and lead time,
        calculate EOQ, ROP, and Total Annual Cost to validate
        all functions work together correctly.
        """
        annual_demand = 5000  # units/year
        ordering_cost = 100   # cost per order
        holding_cost = 2      # cost per unit per year
        daily_demand = annual_demand / 365
        lead_time = 7         # days
        z_score = 1.65        # 95% service level
        demand_std_dev = 10   # units/day

        eoq = calculate_eoq(annual_demand, ordering_cost, holding_cost)
        assert eoq > 0

        safety_stock = calculate_safety_stock(z_score, demand_std_dev, lead_time)
        assert safety_stock > 0

        rop = calculate_reorder_point(daily_demand, lead_time, safety_stock)
        assert rop > safety_stock

        tac = calculate_total_annual_cost(annual_demand, eoq, ordering_cost, holding_cost)
        assert tac > 0

        orders = orders_per_year(annual_demand, eoq)
        assert orders > 0

        assert eoq < annual_demand
        assert rop > 0
        assert tac > 0

    def test_realistic_medicine_scenario(self):
        """
        Test with realistic medicine supply chain values.

        Scenario: Amoxicillin supply for a clinic
        """
        annual_demand = 10000     # units
        ordering_cost = 150       # South African Rand per order
        unit_holding_cost = 1.5   # ZAR per unit per year
        daily_demand = annual_demand / 365
        lead_time_days = 14
        z_score_95 = 1.65
        demand_variability = 15   # units/day

        eoq = calculate_eoq(annual_demand, ordering_cost, unit_holding_cost)
        ss = calculate_safety_stock(z_score_95, demand_variability, lead_time_days)
        rop = calculate_reorder_point(daily_demand, lead_time_days, ss)
        tac = calculate_total_annual_cost(annual_demand, eoq, ordering_cost, unit_holding_cost)
        orders = orders_per_year(annual_demand, eoq)

        assert eoq > 100
        assert rop > ss
        assert tac > 0

        assert 5 < orders < 50  # Reasonable ordering frequency

        