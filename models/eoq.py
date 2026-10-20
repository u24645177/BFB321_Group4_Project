"""
Supply Chain Module: Economic Order Quantity (EOQ) Calculations
"""
import math

# EOQ Calculation Functions
def calculate_eoq(demand, order_cost, hold_cost):
    return math.sqrt((2 * demand * order_cost) / hold_cost)

# Reorder Point Calculation Function
def calculate_reorder_point(average_daily_demand, lead_time_days, safety_stock):
    return (average_daily_demand *lead_time_days) + safety_stock

# Safety Stock Calculation Function
def calculate_safety_stock(z_score, demand_std_dev, lead_time_days):
    return z_score * demand_std_dev * math.sqrt(lead_time_days)

# Total Annual Cost Calculation Function
def calculate_total_annual_cost(demand, order_qty, order_cost, hold_cost):
    ordering = (demand / order_qty) * order_cost
    holding = (order_qty / 2) * hold_cost
    return ordering + holding

if __name__ == "__main__":
    # Example usage of the functions
    # Defining placeholder variables for demonstration purposes. In a real-world scenario, these would beprovided by the user or another part of the system. At the next stage we will link these to the GUI and database to allow for dynamic input and output.
    annual_demand = 12000
    ordering_cost = 50
    holding_cost = 2
    eoq = calculate_eoq(annual_demand, ordering_cost, holding_cost)
    print("Optimal order quantity:", round(eoq, 2))
    
    rop = calculate_reorder_point(10, 5, 20)
    print("Reorder Point with safety stock:", rop)
    
    ss = calculate_safety_stock(1.65, 5, 7)
    print("Safety Stock:", round(ss, 2))
    
    total_cost = calculate_total_annual_cost(annual_demand, eoq, ordering_cost, holding_cost)
    print("Total annual cost at EOQ:", round(total_cost, 2))