# FastBox Delivery Simulator

An advanced package delivery simulation engine that assigns packages to agents based on distance and workload, simulates real-world delays, and logs performance metrics.

---

## 🚀 Key Features (Senior Grade)
- **Modular & OOP Design**: Separated domain models, execution logic, strategies, and utilities.
- **Strategy Pattern**: Extensible agent assignment and traffic delay strategy interfaces. Includes:
  - `NearestAgentStrategy` (standard nearest-neighbor routing)
  - `LoadBalancedStrategy` (distributes load to prevent agent bottlenecking)
- **Parallel processing**: Thread-pool concurrency for running simulations across multiple datasets.
- **Robust CLI**: Configure seed, data folder, strategies, output files, and execution mode via command line arguments.
- **Thread-safe Logging**: Buffered log delivery to ensure clean console outputs when running concurrently.
- **Automated Tests**: Unit tests written using `pytest` to guarantee logic correctness and prevent regressions.

---

## 📂 Project Structure
```
Fastbox-Delivery/
│
├── delivery_simulator.py       # Main CLI entry point
├── README.md                   # This documentation
├── report.json                 # Detailed JSON performance report
├── top_performers.csv          # Top performers summary per dataset
│
├── fastbox_delivery/           # Core library package
│   ├── __init__.py
│   ├── models.py               # Coordinate, Package, and Agent entities
│   ├── strategies.py           # Assignment and Delay Strategy Pattern classes
│   ├── simulator.py            # Simulation execution engine & logger
│   └── main.py                 # File I/O, orchestrator, and CLI definition
│
├── tests/                      # Automated test suite
│   └── test_simulator.py       # pytest modules for models, strategies, and engine
│
└── data/                       # JSON simulation datasets
    ├── base_case.json
    ├── test_case_1.json
    └── ...
```

---

## 🛠️ Installation & Setup
Make sure you have Python 3.8+ installed.

1. Install requirements (optional but recommended for running test suites):
   ```bash
   pip install pytest
   ```

---

## 📈 Running the Simulator
To run the simulation with standard defaults, execute:
```bash
python delivery_simulator.py
```

### Advanced Command Line Options
You can configure the simulation engine using CLI arguments:
```
options:
  -h, --help            show this help message and exit
  --data-dir DATA_DIR   Directory containing JSON datasets (default: data)
  --json-output JSON_OUTPUT
                        Path to save the detailed JSON report (default: report.json)
  --csv-output CSV_OUTPUT
                        Path to save the top performers CSV (default: top_performers.csv)
  --parallel            Enable concurrent processing of datasets (default: False)
  --seed SEED           Random seed for reproducible delay simulation (default: None)
  --strategy {nearest,load_balanced}
                        Agent assignment strategy to use (default: nearest)
  --alpha ALPHA         Workload balancing weight for load_balanced strategy (default: 10.0)
```

#### Examples:
- **Run in parallel mode (high performance)**:
  ```bash
  python delivery_simulator.py --parallel
  ```
- **Run deterministically with a fixed seed**:
  ```bash
  python delivery_simulator.py --seed 1234
  ```
- **Run with the Load-Balanced strategy**:
  ```bash
  python delivery_simulator.py --strategy load_balanced --alpha 15.0
  ```

---

## 🧪 Running Unit Tests
Validate the calculations, parsing structures, and strategies by running the automated test suite:
```bash
python -m pytest
```
