from typing import Literal, Optional
from pydantic import BaseModel, Field

Owner = Literal["commune", "department", "state", "epci", "private", "network"]
ZONE_COLORS = {1: "#6b7a8a", 2: "#9a8f5c", 3: "#c9952c", 4: "#d97706", 5: "#ef4444"}  # level -> map colour


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
