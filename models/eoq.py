"""
Supply Chain Module: Economic Order Quantity (EOQ) Calculations

Functions to still add and implement:
    - calculate_eoq(): Calculate Economic Order Quantity
    - calculate_reorder_point(): Calculate when to reorder
    - calculate_safety_stock(): Calculate buffer stock
    - calculate_total_annual_cost(): Calculate ordering + holding costs
"""
import math

annual_demand = 12000
ordering_cost = 50
holding_cost = 2

def calculate_eoq(demand, order_cost, hold_cost):
    return math.sqrt((2 * demand * order_cost) / hold_cost)

eoq = calculate_eoq(annual_demand, ordering_cost, holding_cost)
orders_per_year = annual_demand / eoq
days_between_orders = 365 / orders_per_year


print("Optimal order quantity:", round(eoq, 2))
print("Orders per year:", round(orders_per_year, 2))
print("Days between orders:", round(days_between_orders, 1))


def calculate_reorder_point(average_daily_demand, lead_time_days, safety_stock):
    return (average_daily_demand *lead_time_days) + safety_stock

Rop1= calculate_reorder_point(10, 5, 20)
Rop2= calculate_reorder_point(10, 5, 0)
print("Reorder Point with safety stock:", Rop1)
print("Reorder Point without safety stock:", Rop2)


def calculate_safety_stock(z_score, demand_std_dev, lead_time_days):
    return z_score * demand_std_dev * math.sqrt(lead_time_days)

ss= calculate_safety_stock(1.65, 5, 7)
print("Safety Stock:", round(ss, 2))

def calculate_total_annual_cost(demand, order_qty, order_cost, hold_cost):
    ordering = (demand / order_qty) * order_cost
    holding = (order_qty / 2) * hold_cost
    return ordering + holding

cost_at_eoq = calculate_total_annual_cost(annual_demand, eoq, ordering_cost, holding_cost)
print("Total annual cost at EOQ:", round(cost_at_eoq, 2))