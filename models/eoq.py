"""
Supply Chain Module: Economic Order Quantity (EOQ) Calculations
"""
import math

# EOQ Calculation Functions
def calculate_eoq(demand, order_cost, hold_cost):
    """
    Calculates the Economic Order Quantity (EOQ) to minimize total inventory costs.

    Formula:
        EOQ = sqrt((2 * Demand * Order_Cost) / Holding_Cost)

    Parameters:
        demand (float): Total annual demand units.
        order_cost (float): Fixed cost per placed order.
        hold_cost (float): Cost to hold one unit of inventory per year.

    Returns:
        float: The optimal order quantity units.

    Assumptions:
        - Holding cost must be greater than 0.
        - Demand cannot be negative.
        - Demand rate and lead time are constant and known.
    """
    if hold_cost <= 0:
        raise ValueError("Holding cost must be greater than 0")
    if demand < 0:
        raise ValueError("Demand cannot be negative")
    return math.sqrt((2 * demand * order_cost) / hold_cost)


def calculate_eoq_with_safety_stock(demand, order_cost, hold_cost, safety_stock):
    """
    Calculates EOQ adjusted for safety stock buffer levels.

    Formula:
        Adjusted EOQ = sqrt((2 * (Demand + Safety_Stock) * Order_Cost) / Holding_Cost)

    Parameters:
        demand (float): Total annual demand units.
        order_cost (float): Fixed cost per placed order.
        hold_cost (float): Annual holding cost per unit.
        safety_stock (float): Additional inventory kept to mitigate stockout risks.

    Returns:
        float: Adjusted optimal order quantity units.

    Assumptions:
        - Demand and ordering costs must be strictly positive.
        - Holding cost and safety stock must be non-negative.
    """
    if demand <= 0:
        raise ValueError("Demand must be a positive number")
    if order_cost <= 0:
        raise ValueError("Ordering cost must be a positive number")
    if hold_cost <= 0 or safety_stock < 0:
        raise ValueError("Holding cost and safety stock must be positive numbers")
    return math.sqrt((2 * (demand + safety_stock) * order_cost) / hold_cost)


# Orders Per Year Calculation Function
def calculate_orders_per_year(demand, order_qty):
    """
    Calculates the expected number of purchase orders placed per year.

    Formula:
        Orders_Per_Year = Demand / Order_Quantity

    Parameters:
        demand (float): Total annual demand units.
        order_qty (float): Units requested per single order batch.

    Returns:
        float: Number of order placement occurrences per year.

    Assumptions:
        - Demand and order quantity must both be positive non-zero values.
    """
    if demand <= 0:
        raise ValueError("Demand must be a positive number")
    if order_qty <= 0:
        raise ValueError("Order quantity must be a positive number")
    return demand / order_qty


# Reorder Point Calculation Function
def calculate_reorder_point(average_daily_demand, lead_time_days, safety_stock):
    """
    Calculates the threshold inventory level that triggers a replenishment order.

    Formula:
        Reorder_Point = (Average_Daily_Demand * Lead_Time_Days) + Safety_Stock

    Parameters:
        average_daily_demand (float): Mean units consumed or issued per day.
        lead_time_days (float): Number of days required between ordering and receiving stock.
        safety_stock (float): Buffer stock held to protect against supply disruptions.

    Returns:
        float: Inventory quantity threshold for reordering.

    Assumptions:
        - Daily demand and safety stock are non-negative.
        - Lead time days must be greater than 0.
    """
    if average_daily_demand < 0:
        raise ValueError("Average daily demand cannot be negative")
    if lead_time_days <= 0:
        raise ValueError("Lead time must be a positive number")
    if safety_stock < 0:
        raise ValueError("Safety stock must be a non-negative number")
    return (average_daily_demand * lead_time_days) + safety_stock


# Safety Stock Calculation Function
def calculate_safety_stock(z_score, demand_std_dev, lead_time_days):
    """
    Calculates required buffer stock based on service level targets and demand variability.

    Formula:
        Safety_Stock = Z_Score * Standard_Deviation_Demand * sqrt(Lead_Time_Days)

    Parameters:
        z_score (float): Statistical factor matching desired cycle service level (e.g., 1.65 for 95%).
        demand_std_dev (float): Standard deviation of daily demand fluctuations.
        lead_time_days (float): Supplier delivery lead time measured in days.

    Returns:
        float: Required safety stock inventory units.

    Assumptions:
        - Lead time is fixed and strictly positive.
        - Demand variation follows a normal statistical distribution.
    """
    if z_score < 0:
        raise ValueError("Z-score cannot be negative")
    if demand_std_dev < 0:
        raise ValueError("Demand standard deviation cannot be negative")
    if lead_time_days <= 0:
        raise ValueError("Lead time must be a positive number")
    return z_score * demand_std_dev * math.sqrt(lead_time_days)


# Total Annual Cost Calculation Function
def calculate_total_annual_cost(demand, order_qty, order_cost, hold_cost):
    """
    Calculates combined annual ordering and holding costs for inventory management.

    Formula:
        Total_Cost = ((Demand / Order_Qty) * Order_Cost) + ((Order_Qty / 2) * Holding_Cost)

    Parameters:
        demand (float): Total annual demand units.
        order_qty (float): Batch size per order.
        order_cost (float): Fixed cost per placed order.
        hold_cost (float): Annual holding cost per unit.

    Returns:
        float: Total annual cost monetary value.

    Assumptions:
        - Average cycle inventory equals Order_Qty / 2.
        - All parameters must be strictly positive non-zero values.
    """
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