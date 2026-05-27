import argparse
import csv
import json
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

from fastbox_delivery.models import Coordinate, Package
from fastbox_delivery.strategies import (
    NearestAgentStrategy,
    LoadBalancedStrategy,
    RandomDelayStrategy,
    ConstantDelayStrategy
)
from fastbox_delivery.simulator import SimulationLogger, DatasetSimulation

# Configure local logger for operational logging (startup, errors, status messages)
logger = logging.getLogger("fastbox_delivery")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def load_dataset(file_path: Path) -> Optional[dict]:
    """
    Loads and returns the raw data from a JSON file, with comprehensive error handling.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON format in {file_path.name}: {e}")
    except Exception as e:
        logger.error(f"Unexpected error loading {file_path.name}: {e}")
    return None


def run_single_simulation(
    file_path: Path,
    args: argparse.Namespace
) -> Optional[Tuple[str, dict, Optional[dict]]]:
    """
    Runs the delivery simulation on a single dataset file.
    
    Returns:
        A tuple of (dataset_name, report_dict, top_performer_dict) if successful, else None.
    """
    dataset_name = file_path.stem
    raw_data = load_dataset(file_path)
    if not raw_data:
        return None

    # Parse and normalize the dataset attributes
    try:
        warehouses_data = raw_data.get("warehouses", [])
        agents_data = raw_data.get("agents", [])
        packages_data = raw_data.get("packages", [])

        # Parse warehouses
        warehouses = {}
        if isinstance(warehouses_data, list):
            for w in warehouses_data:
                warehouses[w["id"]] = Coordinate.from_sequence(w["location"])
        elif isinstance(warehouses_data, dict):
            for w_id, loc in warehouses_data.items():
                warehouses[w_id] = Coordinate.from_sequence(loc)
        else:
            raise ValueError("warehouses key must be a list or dict")

        # Parse agents
        agents = {}
        if isinstance(agents_data, list):
            for a in agents_data:
                agents[a["id"]] = Coordinate.from_sequence(a["location"])
        elif isinstance(agents_data, dict):
            for a_id, loc in agents_data.items():
                agents[a_id] = Coordinate.from_sequence(loc)
        else:
            raise ValueError("agents key must be a list or dict")

        # Parse packages
        packages = [Package.from_dict(p) for p in packages_data]

    except (KeyError, ValueError, TypeError) as e:
        logger.error(f"Data normalization error in dataset {dataset_name}: {e}")
        return None

    # Instantiate strategies based on config
    if args.strategy == "load_balanced":
        assignment_strategy = LoadBalancedStrategy(alpha=args.alpha)
    else:
        assignment_strategy = NearestAgentStrategy()

    # Use random delay if explicitly enabled or if a random seed is provided
    if getattr(args, "random_delay", False) or args.seed is not None:
        delay_strategy = RandomDelayStrategy(seed=args.seed)
    else:
        delay_strategy = ConstantDelayStrategy(1.0)

    # Use buffered logger for atomic, clean console output
    sim_logger = SimulationLogger(buffered=True)

    # Instantiate and run simulator
    simulation = DatasetSimulation(
        dataset_name=dataset_name,
        warehouses=warehouses,
        agents=agents,
        packages=packages,
        assignment_strategy=assignment_strategy,
        delay_strategy=delay_strategy,
        logger=sim_logger,
        visualize=getattr(args, "visualize", False)
    )

    report = simulation.run()
    
    # Flush buffered simulation output atomically
    sim_logger.flush()

    # Determine top performer details
    best_agent = report.get("best_agent")
    top_performer = None
    if best_agent:
        top_performer = {
            "Dataset": dataset_name,
            "Best Agent": best_agent,
            "Packages Delivered": report[best_agent]["packages_delivered"],
            "Total Distance": report[best_agent]["total_distance"],
            "Efficiency": report[best_agent]["efficiency"]
        }

    return dataset_name, report, top_performer


def main():
    parser = argparse.ArgumentParser(
        description="FastBox Delivery Simulator - Advanced Simulation Engine",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default="data",
        help="Directory containing JSON datasets"
    )
    parser.add_argument(
        "--json-output",
        type=str,
        default="report.json",
        help="Path to save the detailed JSON report"
    )
    parser.add_argument(
        "--csv-output",
        type=str,
        default="top_performers.csv",
        help="Path to save the top performers CSV"
    )
    parser.add_argument(
        "--parallel",
        action="store_true",
        help="Enable concurrent processing of datasets (faster for large datasets)"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducible delay simulation"
    )
    parser.add_argument(
        "--strategy",
        type=str,
        choices=["nearest", "load_balanced"],
        default="nearest",
        help="Agent assignment strategy to use"
    )
    parser.add_argument(
        "--random-delay",
        action="store_true",
        help="Enable random delivery delays (bonus feature)"
    )
    parser.add_argument(
        "--visualize",
        action="store_true",
        help="Visualize routes in ASCII grid maps"
    )
    parser.add_argument(
        "--alpha",
        type=float,
        default=10.0,
        help="Workload balancing weight for load_balanced strategy"
    )

    args = parser.parse_args()

    data_path = Path(args.data_dir)
    if not data_path.exists() or not data_path.is_dir():
        logger.error(f"Data directory '{args.data_dir}' does not exist or is not a directory.")
        return

    # Gather all JSON files in the target directory
    dataset_files = sorted(
        [p for p in data_path.iterdir() if p.is_file() and p.suffix == ".json"],
        key=lambda p: p.name
    )

    if not dataset_files:
        logger.warning(f"No JSON datasets found in '{data_path.resolve()}'")
        return

    final_report = {}
    top_performers = []

    # Run simulations concurrently or sequentially
    if args.parallel:
        logger.info(f"Starting parallel execution for {len(dataset_files)} datasets...")
        with ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(run_single_simulation, file_path, args)
                for file_path in dataset_files
            ]
            for future in futures:
                res = future.result()
                if res:
                    dataset_name, report, top_performer = res
                    final_report[dataset_name] = report
                    if top_performer:
                        top_performers.append(top_performer)
    else:
        logger.info(f"Starting sequential execution for {len(dataset_files)} datasets...")
        for file_path in dataset_files:
            res = run_single_simulation(file_path, args)
            if res:
                dataset_name, report, top_performer = res
                final_report[dataset_name] = report
                if top_performer:
                    top_performers.append(top_performer)

    # Sort final report keys and top performers list to maintain deterministic output formatting
    sorted_final_report = {k: final_report[k] for k in sorted(final_report.keys())}
    top_performers.sort(key=lambda x: x["Dataset"])

    # Export report outputs
    try:
        json_out = Path(args.json_output)
        with open(json_out, "w", encoding="utf-8") as f:
            json.dump(sorted_final_report, f, indent=4)

        csv_out = Path(args.csv_output)
        with open(csv_out, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(
                csvfile,
                fieldnames=["Dataset", "Best Agent", "Packages Delivered", "Total Distance", "Efficiency"]
            )
            writer.writeheader()
            writer.writerows(top_performers)

        print(" SIMULATION COMPLETE!")
        print(f" Report saved: {json_out.resolve()}")
        print(f"Top performers: {csv_out.resolve()}")
        print("\n All datasets processed successfully!")

    except Exception as e:
        logger.error(f"Error while saving output files: {e}")
