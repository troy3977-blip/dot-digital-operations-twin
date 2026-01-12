from dataclasses import dataclass

@dataclass
class KPIResult:
    total_cost: float       # TCO
    access_score: float     # 0–100 proxy for service/access
    resilience_margin: float  # 0–100, higher = more resilient
    roi_score: float        # 0–100 proxy for “is it worth it?”
