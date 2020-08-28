## Technician Vehicle Routing Optimization

ALNS (Adaptive Large Neighborhood Search) initially forked from [here](https://github.com/N-Wouda/ALNS) applied to a real-world problem arising in technician vehicle routing. I added a subclassing structure that models the operational planning of technicians which the ALNS algorithm can interact with. The ALNS algorithm then minimizes the costs arising from:

* Unvisited customers depending on their expected profit
* Vehicle abrasion and fuel
* Overtime depending on the vehicle
