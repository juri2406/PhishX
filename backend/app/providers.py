"""Person 2 integration seam. No training parser or detector is implemented here."""
from dataclasses import dataclass, field
from typing import Protocol
from .schemas import Signal, Explanation


class InvalidURL(ValueError):
    """Person 1's shared parser should raise this for malformed URLs."""


@dataclass
class Prediction:
    normalized_host: str
    phishing_probability: float
    observed_signals: list[Signal]
    matched_brand: str | None = None
    skeleton_distance: float | None = None
    # Contains the exact ordered feature row used for inference, for SHAP.
    context: dict = field(default_factory=dict)


@dataclass
class AttributionResult:
    items: list[Explanation]
    scale: str
    method: str = "tree_shap"
    audit: dict | None = None


class Provider(Protocol):
    version: str
    calibrated: bool

    def predict(self, url: str) -> Prediction: ...
    def explain(self, prediction: Prediction) -> AttributionResult: ...


class FixtureProvider:
    version = "fixture-v1-untrained"
    calibrated = False

    def predict(self, url: str) -> Prediction:
        # Exact lookup only: never pretend fixtures are a general URL classifier.
        records = {
            "https://example.com/": ("example.com", .12, None, None),
            "https://account-check.example/login": ("account-check.example", .73, None, None),
            "https://раypal.example/login": ("xn--ypal-43d9g.example", .86, "PayPal (synthetic fixture)", .0),
            "https://example.com/%6c%6f%67%69%6e": ("example.com", .44, None, None),
        }
        if url not in records:
            raise InvalidURL("Fixture mode supports only the four supplied examples. Choose an example, or connect Person 1's model for arbitrary URLs.")
        host, probability, brand, distance = records[url]
        return Prediction(host, probability, [Signal(name="fixture_only", value=True, description="Sample response for UI testing; no detection or feature extraction was run.")], brand, distance)

    def explain(self, prediction: Prediction) -> AttributionResult:
        return AttributionResult([], "fixture")
