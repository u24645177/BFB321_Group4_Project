"""
Supply Chain Module: Economic Order Quantity (EOQ) Calculations
"""
import math
"""
Defining placeholder variables for demonstration purposes. In a real-world scenario, these would be
provided by the user or another part of the system. At the next stage we will link these to the GUI and database to allow for dynamic input and output.
"""
annual_demand = 12000
ordering_cost = 50
holding_cost = 2

"""EOQ Calculation Functions"""
def calculate_eoq(demand, order_cost, hold_cost):
    return math.sqrt((2 * demand * order_cost) / hold_cost)

"""Calculating EOQ, Orders per Year, and Days Between Orders"""
eoq = calculate_eoq(annual_demand, ordering_cost, holding_cost)
orders_per_year = annual_demand / eoq
days_between_orders = 365 / orders_per_year

"""Printing the results to the console for verification. In a real-world application, these would be returned to the GUI or stored in a database."""
print("Optimal order quantity:", round(eoq, 2))
print("Orders per year:", round(orders_per_year, 2))
print("Days between orders:", round(days_between_orders, 1))

"""Reorder Point Calculation Function"""
def calculate_reorder_point(average_daily_demand, lead_time_days, safety_stock):
    return (average_daily_demand *lead_time_days) + safety_stock


""""Calculating Reorder Point with and without Safety Stock"""
Rop1= calculate_reorder_point(10, 5, 20)
Rop2= calculate_reorder_point(10, 5, 0)

"""Printing the Reorder Point results to the console for verification."""
print("Reorder Point with safety stock:", Rop1)
print("Reorder Point without safety stock:", Rop2)

"""Safety Stock Calculation Function"""
def calculate_safety_stock(z_score, demand_std_dev, lead_time_days):
    return z_score * demand_std_dev * math.sqrt(lead_time_days)

""""Calculating Safety Stock"""
ss= calculate_safety_stock(1.65, 5, 7)

"""Printing the Safety Stock result to the console for verification."""
print("Safety Stock:", round(ss, 2))

""""Total Annual Cost Calculation Function"""
def calculate_total_annual_cost(demand, order_qty, order_cost, hold_cost):
    ordering = (demand / order_qty) * order_cost
    holding = (order_qty / 2) * hold_cost
    return ordering + holding

""""Calculating Total Annual Cost at EOQ"""
cost_at_eoq = calculate_total_annual_cost(annual_demand, eoq, ordering_cost, holding_cost)

""""Printing the Total Annual Cost result to the console for verification."""
print("Total annual cost at EOQ:", round(cost_at_eoq, 2))