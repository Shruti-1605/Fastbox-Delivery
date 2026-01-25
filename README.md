
#  FastBox Delivery Simulator

## Project Overview
The FastBox Delivery Simulator is a Python project that simulates a delivery system where multiple agents deliver packages from warehouses to specified destinations.  

**Objectives:**  
- Assign packages efficiently to agents based on proximity.  
- Calculate total distance traveled by each agent.  
- Measure agent efficiency (distance per package).  
- Identify the best-performing agent for each dataset.  

The solution is designed to be **simple, readable, and logical**, as per the evaluation instructions.

---

## How to Run the Project
1. Make sure Python is installed on your system.  
2. Open terminal/command prompt in the project folder.  
3. Run the command:

```bash
python delivery_simulator.py
```

All JSON datasets in the `data/` folder will be processed automatically.

**Outputs:**
- `report.json` → Detailed agent performance metrics.
- `top_performers.csv` → Best-performing agents per dataset.

## Project Structure
```
delivery_simulator/
│
├── delivery_simulator.py       # Main Python script
├── README.md                   # This documentation
├── report.json                 # Detailed report generated after simulation
├── top_performers.csv          # CSV file with top agents
│
└── data/                       # Folder containing test case JSON files
    ├── base_case.json
    ├── test_case_1.json
    ├── test_case_2.json
    └── ... additional test cases
```

## Input Format
Each JSON file contains:
- **Warehouses**: ID and coordinates [x, y]
- **Agents**: ID and starting coordinates [x, y]
- **Packages**: ID, associated warehouse ID, and destination coordinates [x, y]

**Example JSON (base_case.json):**
```json
{
  "warehouses": [
    {"id": "W1", "location": [0, 0]},
    {"id": "W2", "location": [50, 75]}
  ],
  "agents": [
    {"id": "A1", "location": [5, 5]},
    {"id": "A2", "location": [60, 60]}
  ],
  "packages": [
    {"id": "P1", "warehouse_id": "W1", "destination": [30, 40]}
  ]
}
```

## Output Format
**report.json** → Contains performance metrics per agent per dataset:
- `packages_delivered`
- `total_distance`
- `efficiency`
- `best_agent`

**top_performers.csv** → Top-performing agent per dataset:
- Dataset name
- Best Agent
- Packages Delivered
- Total Distance
- Efficiency

**Example JSON Output (report.json):**
```json
{
  "base_case": {
    "A1": {"packages_delivered": 2, "total_distance": 86.05, "efficiency": 43.03},
    "A2": {"packages_delivered": 2, "total_distance": 74.51, "efficiency": 37.25},
    "A3": {"packages_delivered": 1, "total_distance": 15.25, "efficiency": 15.25},
    "best_agent": "A3"
  }
}
```

## Delivery Logic and Approach
1. Each package is assigned to the **nearest available agent** using Euclidean distance.
2. Agents can deliver **multiple packages**.
3. **Distance formula:**
   ```
   distance = √((x₂-x₁)² + (y₂-y₁)²)
   ```
4. **Efficiency calculation:**
   ```
   efficiency = total_distance / packages_delivered
   ```
5. The agent with the **lowest efficiency** is chosen as the best agent.
6. Packages are delivered in the order they appear in the input JSON.
7. Random delivery delays (0–20%) simulate real-world variability.
8. ASCII visualization shows the route from warehouse to destination.

## Assumptions
To handle ambiguous scenarios:
- Distance is calculated using **Euclidean distance**.
- If multiple agents have the same minimum distance, the **first available agent** is selected.
- Agents can deliver **multiple packages**.
- All warehouse and agent locations are **valid**.
- All packages **must be delivered**; none are dropped.
- Packages are delivered in **input order**.
- Agents remain **available throughout the day**.
- Bonus features (random delay, ASCII visualization) are optional and do not affect core metrics.

## Bonus Features
- Random delivery delay simulation (0–20%)
- ASCII-based route visualization for each package
- Handles multiple test cases automatically
- Exports top-performing agents to CSV (`top_performers.csv`)


