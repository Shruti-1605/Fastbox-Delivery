import pytest
from pathlib import Path
from fastbox_delivery.models import Coordinate, Package, NewAgentInfo
from fastbox_delivery.strategies import NearestAgentStrategy, LoadBalancedStrategy, ConstantDelayStrategy
from fastbox_delivery.simulator import SimulationLogger, DatasetSimulation

def test_coordinate_distance():
    c1 = Coordinate(0.0, 0.0)
    c2 = Coordinate(3.0, 4.0)
    assert c1.distance_to(c2) == 5.0
    assert str(c1) == "[0, 0]"
    
    c3 = Coordinate(1.5, 2.5)
    assert str(c3) == "[1.50, 2.50]"


def test_package_parsing():
    raw = {
        "id": "P1",
        "warehouse_id": "W1",
        "destination": [10, 20]
    }
    pkg = Package.from_dict(raw)
    assert pkg.id == "P1"
    assert pkg.warehouse_id == "W1"
    assert pkg.destination == Coordinate(10, 20)
    assert pkg.new_agent is None


def test_package_parsing_with_new_agent():
    raw = {
        "id": "P2",
        "warehouse_id": "W2",
        "destination": [30, 40],
        "new_agent": {
            "id": "A3",
            "location": [5, 5]
        }
    }
    pkg = Package.from_dict(raw)
    assert pkg.new_agent is not None
    assert pkg.new_agent.id == "A3"
    assert pkg.new_agent.location == Coordinate(5, 5)


def test_nearest_agent_strategy():
    strategy = NearestAgentStrategy()
    agents = {
        "A1": Coordinate(0, 0),
        "A2": Coordinate(10, 10)
    }
    wh_loc = Coordinate(1, 1)
    pkg = Package("P1", "W1", Coordinate(5, 5))
    
    assigned = strategy.assign_agent(agents, wh_loc, pkg)
    assert assigned == "A1"


def test_load_balanced_strategy():
    strategy = LoadBalancedStrategy(alpha=5.0)
    agents = {
        "A1": Coordinate(0, 0),
        "A2": Coordinate(1, 1)
    }
    wh_loc = Coordinate(0, 0)
    pkg = Package("P1", "W1", Coordinate(5, 5))
    
    # First assignment: A1 is closer (distance = 0) vs A2 (distance = 1.41)
    # Delivered count: A1 = 0, A2 = 0
    # Score A1 = 0 + 0 = 0. Score A2 = 1.41 + 0 = 1.41 -> A1 is assigned.
    assigned1 = strategy.assign_agent(agents, wh_loc, pkg)
    assert assigned1 == "A1"
    
    # Second assignment:
    # Delivered count: A1 = 1, A2 = 0
    # Score A1 = 0 + 5*1 = 5. Score A2 = 1.41 + 5*0 = 1.41 -> A2 is assigned.
    assigned2 = strategy.assign_agent(agents, wh_loc, pkg)
    assert assigned2 == "A2"


def test_simulation_run():
    warehouses = {"W1": Coordinate(0, 0)}
    agents = {"A1": Coordinate(1, 1)}
    packages = [
        Package("P1", "W1", Coordinate(3, 3))
    ]
    
    logger = SimulationLogger(buffered=True)
    sim = DatasetSimulation(
        dataset_name="test_dataset",
        warehouses=warehouses,
        agents=agents,
        packages=packages,
        assignment_strategy=NearestAgentStrategy(),
        delay_strategy=ConstantDelayStrategy(1.0),
        logger=logger
    )
    
    report = sim.run()
    assert report["best_agent"] == "A1"
    # A1 distance: from [1,1] to W1 [0,0] = sqrt(2) ~ 1.414
    # from W1 [0,0] to DEST [3,3] = sqrt(18) ~ 4.242
    # Total distance: 1.414 + 4.242 = 5.656 -> round to 2 decimal points = 5.66
    assert report["A1"]["packages_delivered"] == 1
    assert report["A1"]["total_distance"] == 5.66
