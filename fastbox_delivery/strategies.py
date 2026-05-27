from abc import ABC, abstractmethod
import random
from typing import Optional, Dict
from fastbox_delivery.models import Coordinate, Package

class AgentAssignmentStrategy(ABC):
    """Abstract interface defining how agents are assigned to packages."""
    @abstractmethod
    def assign_agent(
        self, 
        agents: Dict[str, Coordinate], 
        warehouse_loc: Coordinate, 
        package: Package
    ) -> str:
        """
        Assign an agent to deliver the package.
        
        Args:
            agents: Dictionary mapping agent IDs to their current Coordinates.
            warehouse_loc: Coordinate of the warehouse where the package is located.
            package: The Package object to deliver.
            
        Returns:
            The ID of the assigned agent.
        """
        pass


class NearestAgentStrategy(AgentAssignmentStrategy):
    """Strategy that assigns the package to the closest agent using Euclidean distance."""
    def assign_agent(
        self, 
        agents: Dict[str, Coordinate], 
        warehouse_loc: Coordinate, 
        package: Package
    ) -> str:
        if not agents:
            raise ValueError("No agents available for assignment")
        
        # Select agent with minimum Euclidean distance to warehouse
        return min(
            agents.keys(),
            key=lambda agent_id: agents[agent_id].distance_to(warehouse_loc)
        )


class LoadBalancedStrategy(AgentAssignmentStrategy):
    """
    Strategy that minimizes a combined score of distance_to_warehouse and workload.
    Helps prevent a single agent from being overworked when multiple agents are close.
    Score = distance + alpha * packages_already_delivered.
    """
    def __init__(self, alpha: float = 10.0):
        self.alpha = alpha
        self.packages_delivered_counts: Dict[str, int] = {}

    def assign_agent(
        self, 
        agents: Dict[str, Coordinate], 
        warehouse_loc: Coordinate, 
        package: Package
    ) -> str:
        if not agents:
            raise ValueError("No agents available for assignment")
            
        # Initialize counts for any agents we haven't seen yet
        for agent_id in agents:
            if agent_id not in self.packages_delivered_counts:
                self.packages_delivered_counts[agent_id] = 0
                
        def scoring_function(agent_id: str) -> float:
            dist = agents[agent_id].distance_to(warehouse_loc)
            delivered = self.packages_delivered_counts[agent_id]
            return dist + self.alpha * delivered

        selected_agent = min(agents.keys(), key=scoring_function)
        self.packages_delivered_counts[selected_agent] += 1
        return selected_agent


class DelayStrategy(ABC):
    """Abstract interface defining distance delay multiplier calculations."""
    @abstractmethod
    def calculate_delay_factor(self, package: Package) -> float:
        """Returns a multiplier for the destination distance (e.g. 1.0 - 1.2)."""
        pass


class RandomDelayStrategy(DelayStrategy):
    """Simulates real-world traffic delay by adding a random delay multiplier."""
    def __init__(self, min_factor: float = 1.0, max_factor: float = 1.2, seed: Optional[int] = None):
        self.min_factor = min_factor
        self.max_factor = max_factor
        self._random = random.Random(seed) if seed is not None else random

    def calculate_delay_factor(self, package: Package) -> float:
        return self._random.uniform(self.min_factor, self.max_factor)


class ConstantDelayStrategy(DelayStrategy):
    """Deterministic delay factor, mostly useful for unit testing and CI."""
    def __init__(self, factor: float = 1.1):
        self.factor = factor

    def calculate_delay_factor(self, package: Package) -> float:
        return self.factor
