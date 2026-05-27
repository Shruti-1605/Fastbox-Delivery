from dataclasses import dataclass
import math
from typing import Optional, Union, List, Tuple

@dataclass(frozen=True)
class Coordinate:
    """
    Represents a 2D coordinate on a grid.
    Supports Euclidean distance calculation and formats coordinates for clean log displays.
    """
    x: float
    y: float

    @classmethod
    def from_sequence(cls, seq: Union[List[float], Tuple[float, float]]) -> "Coordinate":
        """
        Creates a Coordinate instance from a sequence of two numbers.
        
        Args:
            seq: A list or tuple containing two numbers.
            
        Raises:
            ValueError: If the sequence is not of length 2 or contains invalid numbers.
        """
        if not isinstance(seq, (list, tuple)) or len(seq) != 2:
            raise ValueError(f"Coordinate must be a sequence of 2 elements, got {seq}")
        try:
            return cls(x=float(seq[0]), y=float(seq[1]))
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid coordinate elements in {seq}: {e}")

    def to_list(self) -> List[float]:
        """Converts coordinate to a standard list representation."""
        return [self.x, self.y]

    def distance_to(self, other: "Coordinate") -> float:
        """Calculates Euclidean distance to another Coordinate."""
        return math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)

    def __str__(self) -> str:
        """
        Formats the coordinate to string representation [x, y].
        Displays integer representations where applicable, and decimal formatting otherwise.
        """
        x_str = f"{int(self.x)}" if self.x.is_integer() else f"{self.x:.2f}"
        y_str = f"{int(self.y)}" if self.y.is_integer() else f"{self.y:.2f}"
        return f"[{x_str}, {y_str}]"


@dataclass(frozen=True)
class NewAgentInfo:
    """Represents registration details for an agent joining the simulation mid-day."""
    id: str
    location: Coordinate

    @classmethod
    def from_dict(cls, data: dict) -> "NewAgentInfo":
        if "id" not in data or "location" not in data:
            raise ValueError("new_agent data must contain 'id' and 'location'")
        return cls(
            id=str(data["id"]),
            location=Coordinate.from_sequence(data["location"])
        )


@dataclass(frozen=True)
class Package:
    """Represents a delivery package with source warehouse, destination, and potential mid-day agent sign-ups."""
    id: str
    warehouse_id: str
    destination: Coordinate
    new_agent: Optional[NewAgentInfo] = None

    @classmethod
    def from_dict(cls, data: dict) -> "Package":
        wh_id = data.get("warehouse_id") or data.get("warehouse")
        if not wh_id:
            raise ValueError("Package must contain 'warehouse_id' or 'warehouse'")
        
        if "destination" not in data:
            raise ValueError("Package must contain 'destination'")
            
        destination = Coordinate.from_sequence(data["destination"])
        
        new_agent = None
        if "new_agent" in data:
            new_agent = NewAgentInfo.from_dict(data["new_agent"])
            
        return cls(
            id=str(data.get("id", "")),
            warehouse_id=str(wh_id),
            destination=destination,
            new_agent=new_agent
        )
