import threading
from typing import Dict, List, Any
from fastbox_delivery.models import Coordinate, Package
from fastbox_delivery.strategies import AgentAssignmentStrategy, DelayStrategy

class SimulationLogger:
    """Thread-safe logging helper for printing simulation details to stdout or buffering."""
    _lock = threading.Lock()

    def __init__(self, buffered: bool = False):
        self.buffered = buffered
        self.buffer: List[str] = []

    def log(self, message: str):
        """Logs a message thread-safely or buffers it based on the configuration."""
        if self.buffered:
            self.buffer.append(message)
        else:
            with self._lock:
                print(message)

    def flush(self):
        """Flushes the buffered logs to stdout in a single atomic block."""
        if self.buffered and self.buffer:
            content = "\n".join(self.buffer)
            with self._lock:
                print(content)
            self.buffer.clear()


class DatasetSimulation:
    """Simulates package delivery for a single dataset."""
    def __init__(
        self,
        dataset_name: str,
        warehouses: Dict[str, Coordinate],
        agents: Dict[str, Coordinate],
        packages: List[Package],
        assignment_strategy: AgentAssignmentStrategy,
        delay_strategy: DelayStrategy,
        logger: SimulationLogger,
        visualize: bool = False
    ):
        self.dataset_name = dataset_name
        self.warehouses = warehouses
        self.agents = agents.copy()  # Copy agents mapping to avoid mutating external state
        self.packages = packages
        self.assignment_strategy = assignment_strategy
        self.delay_strategy = delay_strategy
        self.logger = logger
        self.visualize = visualize
        
        # Initialize report structure matching legacy schemas
        self.report: Dict[str, Any] = {
            agent_id: {
                "packages_delivered": 0,
                "total_distance": 0.0,
                "efficiency": 0.0
            }
            for agent_id in self.agents
        }

    def run(self) -> Dict[str, Any]:
        """
        Executes the simulation for all packages in the dataset.
        
        Returns:
            A dictionary containing delivery metrics for each agent, plus 'best_agent'.
        """
        self.logger.log(f"\n===== Processing Dataset: {self.dataset_name} =====\n")

        for idx, pkg in enumerate(self.packages, 1):
            # 1. Resolve Warehouse
            if pkg.warehouse_id not in self.warehouses:
                self.logger.log(f" Invalid warehouse data in package {idx}: {pkg.id} (warehouse {pkg.warehouse_id} not found)")
                continue
            wh_loc = self.warehouses[pkg.warehouse_id]

            # 2. Handle mid-day agent joining
            if pkg.new_agent:
                new_id = pkg.new_agent.id
                new_loc = pkg.new_agent.location
                if new_id not in self.agents:
                    self.agents[new_id] = new_loc
                    self.report[new_id] = {
                        "packages_delivered": 0,
                        "total_distance": 0.0,
                        "efficiency": 0.0
                    }
                    self.logger.log(f"** New agent {new_id} joined mid-day at {new_loc}! **")

            # 3. Assign Agent
            try:
                assigned_agent = self.assignment_strategy.assign_agent(self.agents, wh_loc, pkg)
            except ValueError as e:
                self.logger.log(f"No agents available: {e}")
                continue

            agent_start_loc = self.agents[assigned_agent]

            # 4. Distance Calculation
            dist_to_wh = agent_start_loc.distance_to(wh_loc)
            base_dist_to_dest = wh_loc.distance_to(pkg.destination)
            delay_factor = self.delay_strategy.calculate_delay_factor(pkg)
            dist_to_dest = base_dist_to_dest * delay_factor

            # 5. Update agent position and statistics
            self.report[assigned_agent]["total_distance"] += dist_to_wh + dist_to_dest
            self.report[assigned_agent]["packages_delivered"] += 1
            self.agents[assigned_agent] = pkg.destination

            # 6. Log route details matching the legacy visual format
            self.logger.log(f"Package {idx} from {pkg.warehouse_id} at {wh_loc} to {pkg.destination}")
            self.logger.log(f"Assigned Agent: {assigned_agent}")
            self.logger.log(f"Distance to Warehouse: {dist_to_wh:.2f}")
            self.logger.log(f"Distance to Destination (with delay): {dist_to_dest:.2f}")
            self.logger.log(f"Total Distance by {assigned_agent}: {self.report[assigned_agent]['total_distance']:.2f}")
            self.logger.log(f"Packages Delivered by {assigned_agent}: {self.report[assigned_agent]['packages_delivered']}")
            self.logger.log(f"{assigned_agent} {agent_start_loc} --> {pkg.warehouse_id} {wh_loc} --> DEST {pkg.destination}")
            
            # Render and log ASCII path visualization
            if self.visualize:
                map_str = self._render_ascii_route(assigned_agent, agent_start_loc, pkg.warehouse_id, wh_loc, pkg.destination)
                self.logger.log(map_str)

            self.logger.log("-" * 50)

        # Calculate efficiency statistics and determine the best-performing agent
        best_agent = None
        best_eff = float("inf")

        for agent_id, stats in list(self.report.items()):
            if stats["packages_delivered"] > 0:
                stats["total_distance"] = round(stats["total_distance"], 2)
                stats["efficiency"] = round(stats["total_distance"] / stats["packages_delivered"], 2)
                if stats["efficiency"] < best_eff:
                    best_eff = stats["efficiency"]
                    best_agent = agent_id
            else:
                stats["efficiency"] = 0.0
                stats["total_distance"] = round(stats["total_distance"], 2)

        self.report["best_agent"] = best_agent

        # Log completion summaries
        self.logger.log(f"\n--- Summary for Dataset {self.dataset_name} ---")
        for a, s in self.report.items():
            if a != "best_agent":
                self.logger.log(f"Agent {a}: Packages={s['packages_delivered']}, Distance={s['total_distance']}, Efficiency={s['efficiency']}")
        self.logger.log(f"Best Agent: {best_agent}")
        self.logger.log("=" * 70)

        return self.report

    def _render_ascii_route(
        self,
        agent_id: str,
        agent_start: Coordinate,
        wh_id: str,
        wh_loc: Coordinate,
        dest: Coordinate
    ) -> str:
        """Generates an ASCII grid map representing the coordinates and the route path."""
        all_coords = []
        for w_loc in self.warehouses.values():
            all_coords.append(w_loc)
        for a_loc in self.agents.values():
            all_coords.append(a_loc)
        all_coords.extend([agent_start, wh_loc, dest])

        xs = [c.x for c in all_coords]
        ys = [c.y for c in all_coords]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)

        span_x = max_x - min_x
        span_y = max_y - min_y

        rows, cols = 10, 20
        grid = [[" . " for _ in range(cols)] for _ in range(rows)]

        def get_grid_pos(coord):
            col_idx = int((coord.x - min_x) / span_x * (cols - 1)) if span_x > 0 else 0
            row_idx = (rows - 1) - int((coord.y - min_y) / span_y * (rows - 1)) if span_y > 0 else 0
            return max(0, min(cols - 1, col_idx)), max(0, min(rows - 1, row_idx))

        a_col, a_row = get_grid_pos(agent_start)
        w_col, w_row = get_grid_pos(wh_loc)
        d_col, d_row = get_grid_pos(dest)

        # Draw path from agent start to warehouse
        def draw_line(c1, r1, c2, r2, marker):
            steps = max(abs(c2 - c1), abs(r2 - r1))
            if steps == 0:
                grid[r1][c1] = marker
                return
            for step in range(steps + 1):
                t = step / steps
                c = int(c1 + t * (c2 - c1))
                r = int(r1 + t * (r2 - r1))
                grid[r][c] = marker

        draw_line(a_col, a_row, w_col, w_row, " * ")
        draw_line(w_col, w_row, d_col, d_row, " # ")

        # Place inactive warehouses and agents
        for other_w_id, other_w_loc in self.warehouses.items():
            if other_w_id != wh_id:
                oc, or_ = get_grid_pos(other_w_loc)
                num = other_w_id[1:] if len(other_w_id) > 1 else ""
                grid[or_][oc] = f"W{num}".ljust(3)

        for other_a_id, other_a_loc in self.agents.items():
            if other_a_id != agent_id:
                oc, or_ = get_grid_pos(other_a_loc)
                num = other_a_id[1:] if len(other_a_id) > 1 else ""
                grid[or_][oc] = f"A{num}".ljust(3)

        # Place active entities (overriding path/inactive markers)
        a_num = agent_id[1:] if len(agent_id) > 1 else ""
        grid[a_row][a_col] = f"A{a_num}*".ljust(3)
        
        w_num = wh_id[1:] if len(wh_id) > 1 else ""
        grid[w_row][w_col] = f"W{w_num}".ljust(3)
        
        grid[d_row][d_col] = "DST"

        border = "+" + "-" * (cols * 3 + 2) + "+"
        lines = ["\nASCII Route Map:", border]
        for row_data in grid:
            row_str = "".join(row_data)
            lines.append(f"| {row_str} |")
        lines.append(border)
        lines.append(f"Legend: A{a_num}*=Agent Start, W{w_num}=Warehouse, DST=Destination, *=To WH, #=To DST")
        return "\n".join(lines)
