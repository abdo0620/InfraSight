from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator

Owner = Literal["commune", "department", "state", "epci", "private", "network"]
ZONE_COLORS = {1: "#6b7a8a", 2: "#9a8f5c", 3: "#c9952c", 4: "#d97706", 5: "#ef4444"}  # level -> map colour


def _box(v):
    """Damage box [x1, y1, x2, y2] as fractions of the photo; anything unusable becomes None (no red zone)."""
    if v is None:
        return None
    try:
        x1, y1, x2, y2 = (min(1.0, max(0.0, float(c))) for c in v)
    except (TypeError, ValueError):
        return None
    return [x1, y1, x2, y2] if x2 - x1 > 0.01 and y2 - y1 > 0.01 else None


class PotentialEvent(BaseModel):
    event: str
    likelihood: Literal["low", "medium", "high"]
    impact: str


class Consequences(BaseModel):
    danger_type: str                      # e.g. "road blocked", "risk of falling"
    blocked_access: bool = False
    potential_events: list[PotentialEvent] = []
    vulnerable_people: str = ""
    immediate_measures: list[str] = []


class DangerZone(BaseModel):
    shape: Literal["point", "street", "area"] = "point"   # how the map draws it, see ZONE_RULES in services/ai.py
    radius_m: float                       # circle radius, or length of street affected for "street"
    level: int = Field(ge=1, le=5)        # same scale as severity -> colour
    description: str = ""
    lat: Optional[float] = None           # TODO: fill from the citizen's pin / geocoding
    lng: Optional[float] = None

    @property
    def color(self) -> str:
        return ZONE_COLORS[self.level]


class Triage(BaseModel):
    title: str
    type: str
    severity: int = Field(ge=1, le=5)
    urgency: int = Field(ge=1, le=5)
    owner: Owner
    summary: str
    duplicate_of: Optional[str] = None
    consequences: Consequences
    danger_zone: DangerZone
    damage_box: Optional[list[float]] = None   # where the damage is on the photo, for the red zone

    _check_box = field_validator("damage_box", mode="before")(_box)


class Authority(BaseModel):
    primary: str
    secondary: list[str] = []
    contact_reason: str = ""


class Regulatory(BaseModel):
    procurement: str = ""
    authorizations: list[str] = []
    council_vote: bool = False
    legal_notes: list[str] = []


class Cost(BaseModel):
    min: float = 0
    max: float = 0
    basis: str = ""


class Action(BaseModel):
    step: str
    owner: str
    deadline: str


class Report(BaseModel):
    type: str
    severity: int = Field(ge=1, le=5)
    severity_reason: str
    urgency: str
    response_time: str
    authority: Authority
    ownership_assessment: str
    regulatory: Regulatory
    cost: Cost
    risks: list[str] = []
    actions: list[Action] = []
    citizen_message: str = ""
    consequences: Consequences
    danger_zone: DangerZone


class SizeEstimate(BaseModel):
    """Real size of the damage, estimated by the AI from the photo (and the SAM outline when available)."""
    width_m: float = 0
    length_m: float = 0
    depth_cm: Optional[float] = None
    area_m2: float = 0
    basis: str = ""                       # which visible references the estimate relies on
    confidence: Literal["low", "medium", "high"] = "low"
    box: Optional[list[float]] = None     # where the damage is on the photo, when SAM did not outline it

    _check_box = field_validator("box", mode="before")(_box)


class RepairCheck(BaseModel):
    """Before / after photo comparison at closing time."""
    verdict: Literal["repaired", "partial", "not_repaired", "unclear"]
    explanation: str
    remaining_issues: list[str] = []


class HotspotForecast(BaseModel):
    street: str
    risk: Literal["low", "medium", "high"]
    expected_problem: str
    reason: str
    preventive_action: str
    budget_eur: float = 0


class Forecast(BaseModel):
    summary: str
    hotspots: list[HotspotForecast] = []
