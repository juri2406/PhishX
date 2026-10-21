from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator


class ScanRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    url: str = Field(min_length=1, max_length=2048)

    @field_validator("url")
    @classmethod
    def check_envelope(cls, value: str) -> str:
        if value != value.strip() or any(c.isspace() or ord(c) < 32 or ord(c) == 127 for c in value):
            raise ValueError("Remove whitespace and control characters from the URL.")
        if not value.lower().startswith(("http://", "https://")):
            raise ValueError("Include an http:// or https:// scheme.")
        return value


class Signal(BaseModel):
    name: str
    value: str | float | bool
    description: str


class Explanation(BaseModel):
    feature: str
    observed_value: str | float | bool
    contribution: float = Field(gt=0, allow_inf_nan=False)
    reason: str


class ScanResponse(BaseModel):
    submitted_url: str
    normalized_host: str
    phishing_probability: float = Field(ge=0, le=1, allow_inf_nan=False)
    risk_score: int = Field(ge=0, le=100)
    risk_level: Literal["Low", "Medium", "High", "Critical"]
    matched_brand: str | None = None
    skeleton_distance: float | None = Field(default=None, ge=0, le=1)
    observed_signals: list[Signal]
    explanation_items: list[Explanation] = Field(max_length=3)
    explanation_status: Literal["available", "unavailable", "fixture"]
    explanation_message: str | None = None
    explanation_scale: str | None = None
    explanation_method: str | None = None
    explanation_audit: dict | None = None
    model_used: Literal["classical", "cascade"] = "classical"
    cascade_status: Literal["not_implemented", "available"] = "not_implemented"
    model_version: str
    mode: Literal["fixture", "model"]
    probability_calibrated: bool = False
    unavailable_signals: list[str] = Field(default_factory=lambda: ["Domain age", "DNS", "TLS validity", "Redirects"])
    timings_ms: dict[str, float]


class LiveCheck(BaseModel):
    name: Literal["DNS", "TLS validity", "Redirects", "Domain age"]
    status: Literal["available", "unavailable", "blocked", "not_applicable"]
    value: str | int | float | bool | None = None
    message: str | None = None


class RedirectHop(BaseModel):
    scheme: Literal["http", "https"]
    host: str
    http_status: int


class LiveSignalsResponse(BaseModel):
    checks: list[LiveCheck]
    redirect_chain: list[RedirectHop]
    checked_at: str
    affects_model_score: Literal[False] = False


def score_probability(probability: float) -> tuple[int, str]:
    import math
    if not math.isfinite(probability) or not 0 <= probability <= 1:
        raise ValueError("Provider returned an invalid phishing probability.")
    score = round(100 * probability)
    return score, "Low" if score <= 30 else "Medium" if score <= 60 else "High" if score <= 80 else "Critical"
