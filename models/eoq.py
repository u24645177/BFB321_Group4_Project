"""
Supply Chain Module: Economic Order Quantity (EOQ) Calculations
"""
import math

# EOQ Calculation Functions
def calculate_eoq(demand, order_cost, hold_cost):
    if hold_cost <= 0:
        raise ValueError("Holding cost must be greater than 0")
    if demand < 0:
        raise ValueError("Demand cannot be negative")
    return math.sqrt((2 * demand * order_cost) / hold_cost)


def calculate_eoq_with_safety_stock(demand, order_cost, hold_cost, safety_stock):
    if demand <= 0:
        raise ValueError("Demand must be a positive number")
    if order_cost <= 0:
        raise ValueError("Ordering cost must be a positive number")
    if hold_cost <= 0 or safety_stock < 0:
        raise ValueError("Holding cost and safety stock must be positive numbers")
    return math.sqrt((2 * (demand + safety_stock) * order_cost) / hold_cost)

# Orders Per Year Calculation Function
def calculate_orders_per_year(demand, order_qty):
    if demand <= 0:
        raise ValueError("Demand must be a positive number")
    if order_qty <= 0:
        raise ValueError("Order quantity must be a positive number")
    return demand / order_qty

# Reorder Point Calculation Function
def calculate_reorder_point(average_daily_demand, lead_time_days, safety_stock):
    if average_daily_demand <= 0:
        raise ValueError("Average daily demand must be a positive number")
    if lead_time_days <= 0:
        raise ValueError("Lead time must be a positive number")
    if safety_stock < 0:
        raise ValueError("Safety stock must be a non-negative number")
    return (average_daily_demand * lead_time_days) + safety_stock

# Safety Stock Calculation Function
def calculate_safety_stock(z_score, demand_std_dev, lead_time_days):
    if z_score <= 0:
        raise ValueError("Z-score must be a positive number")
    if demand_std_dev <= 0:
        raise ValueError("Demand standard deviation must be a positive number")
    if lead_time_days <= 0:
        raise ValueError("Lead time must be a positive number")
    return z_score * demand_std_dev * math.sqrt(lead_time_days)

# Total Annual Cost Calculation Function
def calculate_total_annual_cost(demand, order_qty, order_cost, hold_cost):
    if demand <= 0:
        raise ValueError("Demand must be a positive number")
    if order_qty <= 0:
        raise ValueError("Order quantity must be a positive number")
    if order_cost <= 0:
        raise ValueError("Ordering cost must be a positive number")
    if hold_cost <= 0:
        raise ValueError("Holding cost must be a positive number")
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

    n_orders = calculate_orders_per_year(annual_demand, eoq)
    print("Number of orders per year:", round(n_orders, 2)) 

    days_between_orders = 365 / n_orders
    print("Days between orders:", round(days_between_orders, 2))
        
    rop = calculate_reorder_point(10, 5, 20)
    print("Reorder Point with safety stock:", rop)
    
    ss = calculate_safety_stock(1.65, 5, 7)
    print("Safety Stock:", round(ss, 2))
    
    total_cost = calculate_total_annual_cost(annual_demand, eoq, ordering_cost, holding_cost)
    print("Total annual cost at EOQ:", round(total_cost, 2))

