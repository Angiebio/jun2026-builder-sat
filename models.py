# models.py — Pydantic interfaces for the Antiques Inference Engine
# Date: 27JUN2026
# Version: 1.0
# Technical: Defines strictly-typed schemas for data exchange between agents.
# Philosophical: Standard structures are the architecture of shared truth. Without schemas, language drifts.

from pydantic import BaseModel, Field
from typing import List, Literal, Optional

# Strictly typed taxonomy to prevent Granite from inventing arbitrary categories
PowerOrComputePath = Literal[
    "galvanic_dc",
    "rotational_mechanical_power",
    "steam_rotational_power",
    "human_mechanical_power",
    "punched_card_parallel_binary",
    "mechanical_decimal_compute",
    "electromagnetic_switching",
    "silicon_microprocessor_compute",  # Added per Flame2's audit of TI-82 and Nokia microprocessors
    "optical_or_measurement_only",
    "decorative_or_unknown"
]

class ArtifactObservation(BaseModel):
    artifact_guess: str = Field(..., description="Likely name of the antique.")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score [0.0, 1.0]")
    visible_features: List[str] = Field(default_factory=list)
    alternate_guesses: List[str] = Field(default_factory=list)
    power_or_compute_path: PowerOrComputePath
    suggested_crop_roi: Optional[List[int]] = Field(
        None, 
        description="Optional bounding box [x1, y1, x2, y2] normalized to [0, 1000] scale for zooming."
    )

class ResearchNotes(BaseModel):
    artifact_family: str
    era: str
    mechanism: str
    historical_notes: List[dict] = Field(default_factory=list)  # list of {"claim": str, "source": str}
    usable_assumptions: List[dict] = Field(default_factory=list)  # list of {"parameter": str, "value": float, "confidence": str}

class MathResult(BaseModel):
    path: PowerOrComputePath
    mode: Literal["power", "compute", "unsupported"]
    input_value: float = Field(..., description="The input value (watts or ops_per_second).")
    input_unit: Literal["watts", "ops_per_second", "none"]
    units_for_ai_hello: float = Field(..., description="Number of units needed to run AI.")
    potatoes_equivalent: float = Field(..., description="Equivalent value in potato batteries.")
    cyclists_equivalent: float = Field(..., description="Equivalent value in cycling humans.")
    time_seconds: float = Field(..., description="Execution time in seconds (for compute path).")
    time_years: float = Field(..., description="Execution time in years (for compute path).")
    can_evaluate: bool = Field(..., description="True if the path can be calculated.")
    calculation_log: List[str] = Field(default_factory=list)

class QCResult(BaseModel):
    passed: bool = Field(..., alias="pass", description="True if the run passes verification.")
    reason: str = Field(..., description="The reason for pass/fail classification.")
    route_to: Optional[Literal["artifact_goblin", "sherlock_ohms", "potato_accountant"]] = Field(
        None,
        description="The agent to route back to if failed."
    )

    model_config = {
        "populate_by_name": True
    }
