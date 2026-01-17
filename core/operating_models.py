from enum import Enum
from dataclasses import dataclass

class OperatingModelType(str, Enum):
    LEAN = "Lean"
    BALANCED = "Balanced"
    RESILIENT = "Resilient"

@dataclass
class OperatingModelConfig:
    name: str
    staffing_level: float        # relative 0–1
    vendor_support: float        # 0–1
    digital_penetration: float   # 0–1
    risk_tolerance: float        # 0–1

def get_default_operating_models():
    return {
        OperatingModelType.LEAN: OperatingModelConfig(
            name="Lean",
            staffing_level=0.7,
            vendor_support=0.2,
            digital_penetration=0.4,
            risk_tolerance=0.8,
        ),
        OperatingModelType.BALANCED: OperatingModelConfig(
            name="Balanced",
            staffing_level=0.85,
            vendor_support=0.4,
            digital_penetration=0.6,
            risk_tolerance=0.5,
        ),
        OperatingModelType.RESILIENT: OperatingModelConfig(
            name="Resilient",
            staffing_level=1.0,
            vendor_support=0.6,
            digital_penetration=0.8,
            risk_tolerance=0.3,
        ),
    }