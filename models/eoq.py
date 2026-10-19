"""
Supply Chain Module: Economic Order Quantity (EOQ) Calculations

This module provides functions to calculate optimal inventory management metrics
for the MedSync medicine supply chain system.

Functions:
    - calculate_eoq(): Calculate Economic Order Quantity
    - calculate_reorder_point(): Calculate when to reorder
    - calculate_safety_stock(): Calculate buffer stock
    - calculate_total_annual_cost(): Calculate ordering + holding costs
"""

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
    """
    pass


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
    """
    pass


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
    """
    pass


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
    """
    pass