"""
Supply Chain Module: Economic Order Quantity (EOQ) Calculations

This module provides functions to calculate optimal inventory management metrics
for the MedSync medicine supply chain system.

It is a standalone module: it does NOT import Flask, the database, or any
framework code. The API layer (Step 4) calls these functions directly.

Replenishment policy:
    These functions together define HOW reorder thresholds and order quantities
    are determined, rather than using predefined reorder levels. Order quantity
    comes from the EOQ; the reorder point is calculated from average demand,
    supplier lead time and safety stock; safety stock is sized from demand
    variability and the target service level. In other words, the thresholds
    shown on the dashboard are calculated, not hard-coded.

Functions:
    - calculate_eoq(): Calculate Economic Order Quantity
    - calculate_reorder_point(): Calculate when to reorder
    - calculate_safety_stock(): Calculate buffer stock
    - calculate_total_annual_cost(): Calculate ordering + holding costs
    - orders_per_year(): Calculate how many orders are placed per year
"""

import math


def calculate_eoq(annual_demand, ordering_cost, holding_cost):
    """
    Calculate Economic Order Quantity (EOQ).

    EOQ determines the optimal order quantity that minimizes total inventory costs.

    Args:
        annual_demand (float): Annual demand in units
        ordering_cost (float): Cost per order
        holding_cost (float): Cost per unit per year

    Returns:
        float: Optimal order quantity (units)

    Formula:
        EOQ = √(2 × D × S / H)
        where D = annual demand, S = ordering cost, H = holding cost

    Assumptions:
        - Demand is known and constant throughout the year.
        - Ordering cost and holding cost per unit are fixed.
        - The full order quantity arrives in a single delivery.
        - No stockouts and no quantity (bulk) discounts.
    """
    if holding_cost <= 0 or ordering_cost < 0 or annual_demand < 0:
        raise ValueError("holding_cost must be positive; ordering_cost and annual_demand must be non-negative")

    eoq = math.sqrt((2 * annual_demand * ordering_cost) / holding_cost)
    return eoq


def calculate_reorder_point(average_daily_demand, lead_time_days, safety_stock):
    """
    Calculate Reorder Point (ROP).

    ROP tells us when to place a new order to avoid stockouts.

    Args:
        average_daily_demand (float): Average daily demand in units
        lead_time_days (int): Supplier lead time in days
        safety_stock (float): Safety stock buffer in units

    Returns:
        float: Reorder point in units

    Formula:
        ROP = (Average Daily Demand × Lead Time) + Safety Stock

    Assumptions:
        - Average daily demand and supplier lead time are reasonably stable.
        - Safety stock absorbs the normal variation in demand during lead time.
    """
    if average_daily_demand < 0 or lead_time_days < 0 or safety_stock < 0:
        raise ValueError("All parameters must be non-negative")

    rop = (average_daily_demand * lead_time_days) + safety_stock
    return rop


def calculate_safety_stock(z_score, demand_std_dev, lead_time_days):
    """
    Calculate Safety Stock (SS).

    Safety stock is buffer inventory to protect against demand variability.

    Args:
        z_score (float): Z-score for service level (1.65 for 95%, 2.33 for 99%)
        demand_std_dev (float): Standard deviation of daily demand
        lead_time_days (int): Supplier lead time in days

    Returns:
        float: Safety stock in units

    Formula:
        SS = Z × σ × √(Lead Time)
        where Z = z-score, σ = std dev, Lead Time = days

    Assumptions:
        - Daily demand is roughly normally distributed.
        - Lead time is constant; only demand varies.
        - The z-score matches the chosen service level (e.g. 1.65 = 95%).
    """
    if z_score < 0 or demand_std_dev < 0 or lead_time_days < 0:
        raise ValueError("All parameters must be non-negative")

    safety_stock = z_score * demand_std_dev * math.sqrt(lead_time_days)
    return safety_stock


def calculate_total_annual_cost(annual_demand, order_quantity, ordering_cost, holding_cost):
    """
    Calculate Total Annual Inventory Cost.

    Combines ordering costs and holding costs.

    Args:
        annual_demand (float): Annual demand in units
        order_quantity (float): Order quantity per order
        ordering_cost (float): Cost per order
        holding_cost (float): Cost per unit per year

    Returns:
        float: Total annual cost in currency

    Formula:
        TAC = (D/Q × S) + (Q/2 × H)
        where D = demand, Q = order qty, S = ordering cost, H = holding cost

    Assumptions:
        - Demand is constant and ordering/holding costs are fixed.
        - Average inventory held is half the order quantity (Q/2).
        - Costs scale linearly with quantity.
    """
    if order_quantity <= 0 or annual_demand < 0 or ordering_cost < 0 or holding_cost < 0:
        raise ValueError("order_quantity must be positive; others must be non-negative")

    ordering_total = (annual_demand / order_quantity) * ordering_cost
    holding_total = (order_quantity / 2) * holding_cost
    total_annual_cost = ordering_total + holding_total

    return total_annual_cost


def orders_per_year(annual_demand, order_quantity):
    """
    Calculate the number of orders placed per year.

    Tells us how often we reorder. Usually paired with EOQ as the order quantity.

    Args:
        annual_demand (float): Annual demand in units
        order_quantity (float): Units per order (often the EOQ result)

    Returns:
        float: Number of orders placed per year

    Formula:
        Orders per year = D / Q
        where D = annual demand, Q = order quantity

    Assumptions:
        - Demand is spread evenly across the year.
        - Every order is the same size (the order quantity).
    """
    if order_quantity <= 0 or annual_demand < 0:
        raise ValueError("order_quantity must be positive; annual_demand must be non-negative")

    return annual_demand / order_quantity
