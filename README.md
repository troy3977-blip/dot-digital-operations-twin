# DOT ReadME

Modeling & Optimization
This project implements a Digital Workforce Twin, a decision support system that simulates how staffing, automation, vendor mix, shrinkage, and demand shocks impact service performance, cost to serve, and operational resilience in customer support environments.

Modeling Approach
Workforce performance is modeled using a simplified M/M/n queueing formulation (Erlang-C) calibrated to an 80/60 service level target and a 420s AHT assumption. Demand shocks scale inbound contact volume, while automation reduces effective arrival rates via digital deflection. Shrinkage reduces effective capacity, and vendor mix influences cost and labor flexibility. Key KPIs include:
    Service Level (80/60)
    Avg Wait Time
    Backlog (Queue Size)
    Occupancy
    Cost per Hour
    Resilience Margin (Capacity Headroom)
These metrics expose non-linear trade-offs between labor allocation, digital penetration, and operational performance under stress conditions.

Optimization Layer
To support prescriptive decision making, the system includes an optimization layer that searches the workforce configuration space to identify optimal or non-dominated policies under user-defined objectives. Three optimization modes are implemented:

    Minimize Cost Subject to Service Constraint
        Find the cheapest configuration that achieves or exceeds a target service level under a specified demand shock.
    Maximize Service Subject to Cost Constraint
        Identify the highest-performing configuration within a defined operating budget, preferring policies with higher resilience when service levels are tied.
    Pareto Frontier (Cost vs Service)
        Compute a non-dominated frontier of workforce policies to reveal optimal cost–service trade-offs and eliminate dominated options.
        
The optimization layer is deliberately transparent and explainable, using structured grid search over key levers. This makes trade-offs interpretable, comparable, and suitable for stakeholder decision-making across strategy, operations, and workforce planning contexts.
