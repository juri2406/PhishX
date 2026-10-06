"""Optional binary tree SHAP adapter. Install requirements-model.txt to use.

Person 1 must supply the exact model feature order, transformed numeric row,
phishing label, output scale and a function computing that output for additivity.
No guessed class index, scale or fallback indicator explanations.
"""
from .providers import AttributionResult
from .schemas import Explanation


class TreeShapAdapter:
    def __init__(self, model, feature_names, phishing_label, scale, output_fn, reason_map, single_output_label=None):
        import shap
        if len(set(feature_names)) != len(feature_names) or not feature_names:
            raise ValueError("Feature schema must be nonempty and unique")
        classes = list(model.classes_)
        if len(classes) != 2 or phishing_label not in classes:
            raise ValueError("An explicit binary phishing class is required")
        if scale not in {"probability", "raw", "log_odds"}:
            raise ValueError("Confirm the model output scale")
        if hasattr(model, "feature_names_in_") and list(model.feature_names_in_) != list(feature_names):
            raise ValueError("Model feature names disagree with schema")
        self.explainer = shap.TreeExplainer(model)
        self.names = list(feature_names)
        self.index = classes.index(phishing_label)
        self.scale, self.output_fn, self.reasons = scale, output_fn, reason_map
        self.single_output_label, self.phishing_label = single_output_label, phishing_label

    def explain(self, features):
        import numpy as np
        if list(features) != self.names:
            raise ValueError("Inference features do not match the ordered model schema")
        row = np.array([[features[name] for name in self.names]], dtype=float)
        if not np.isfinite(row).all():
            raise ValueError("Nonfinite feature values")
        result = self.explainer(row)
        values, base = np.asarray(result.values), np.asarray(result.base_values)
        if values.shape == (1, len(self.names), 2):
            contributions, baseline = values[0, :, self.index], base.reshape(1, 2)[0, self.index]
        elif values.shape == (1, len(self.names)) and self.single_output_label == self.phishing_label:
            contributions, baseline = values[0], base.reshape(-1)[0]
        else:
            raise ValueError("Ambiguous SHAP output/class shape; confirm the single-output label")
        expected = float(self.output_fn(row))
        if not np.isfinite(contributions).all() or not np.isfinite(expected) or not np.isclose(baseline + contributions.sum(), expected, rtol=1e-4, atol=1e-5):
            raise ValueError("SHAP additivity/output scale check failed")
        items = []
        for name, contribution in zip(self.names, contributions):
            if contribution > 0:
                reason = self.reasons.get(name, f"The observed {name.replace('_', ' ')} increased the model's phishing output.")
                items.append(Explanation(feature=name, observed_value=float(features[name]), contribution=float(contribution), reason=reason))
        return AttributionResult(sorted(items, key=lambda x: x.contribution, reverse=True)[:3], self.scale)
