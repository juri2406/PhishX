import importlib
import logging
import os
from contextlib import asynccontextmanager
from time import perf_counter
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from .providers import FixtureProvider, InvalidURL
from .schemas import ScanRequest, ScanResponse, score_probability

logger = logging.getLogger("phishx")


def create_app(provider=None, mode=None):
    selected_mode = mode or os.getenv("PHISHX_MODE", "model")
    if selected_mode not in {"fixture", "model"}:
        raise ValueError("PHISHX_MODE must be fixture or model")

    @asynccontextmanager
    async def lifespan(app):
        app.state.provider = provider
        if app.state.provider is None:
            if selected_mode == "fixture":
                app.state.provider = FixtureProvider()
            else:
                factory = os.getenv("PHISHX_PROVIDER", "")
                if factory:
                    try:
                        module, name = factory.split(":")
                        app.state.provider = getattr(importlib.import_module(module), name)()
                    except Exception:
                        logger.exception("Model provider failed to initialize")
        yield

    app = FastAPI(title="PhishX", version="0.1.0", lifespan=lifespan)
    app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], allow_methods=["GET", "POST"], allow_headers=["Content-Type"])

    def error(status, code, message, details=None):
        return JSONResponse(status_code=status, content={"error": {"code": code, "message": message, "details": details or []}})

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError):
        return error(422, "INVALID_REQUEST", "Enter a URL with an http:// or https:// scheme, without spaces (maximum 2048 characters).", [{"field": ".".join(str(p) for p in e["loc"]), "message": e["msg"]} for e in exc.errors()])

    @app.get("/health")
    def health():
        active = app.state.provider
        return {"status": "ok" if active else "not_ready", "ready": active is not None, "mode": selected_mode, "model_version": getattr(active, "version", None), "cascade_status": "not_implemented"}

    @app.post("/scan", response_model=ScanResponse)
    def scan(body: ScanRequest):
        active = app.state.provider
        if active is None:
            return error(503, "MODEL_NOT_READY", "Person 1's model provider is not connected. Use fixture mode for UI development.")
        start = perf_counter()
        try:
            prediction = active.predict(body.url)
            score, band = score_probability(prediction.phishing_probability)
        except InvalidURL as exc:
            return error(422, "INVALID_URL", str(exc))
        except Exception:
            logger.exception("Inference failed (submitted URL omitted)")
            return error(500, "INFERENCE_FAILED", "The model could not complete this scan. Check the backend logs.")
        predicted = perf_counter()
        items, scale, message = [], None, None
        status = "fixture" if selected_mode == "fixture" else "unavailable"
        if selected_mode == "fixture":
            message = "Sample data only. SHAP explanations require Person 1's frozen model."
        else:
            try:
                explanation = active.explain(prediction)
                # Validate all items, then show the strongest positive contributions.
                from .schemas import Explanation
                valid = [Explanation.model_validate(x, from_attributes=True) for x in explanation.items]
                if not explanation.scale:
                    raise ValueError("Explanation output scale is missing")
                items = sorted(valid, key=lambda item: item.contribution, reverse=True)[:3]
                scale, status = explanation.scale, "available"
            except Exception:
                logger.exception("SHAP explanation failed")
                message = "Prediction succeeded, but model explanations are unavailable. No reasons were substituted."
        explained = perf_counter()
        try:
            return ScanResponse(submitted_url=body.url, normalized_host=prediction.normalized_host, phishing_probability=prediction.phishing_probability, risk_score=score, risk_level=band, matched_brand=prediction.matched_brand, skeleton_distance=prediction.skeleton_distance, observed_signals=prediction.observed_signals, explanation_items=items, explanation_status=status, explanation_message=message, explanation_scale=scale, model_version=active.version, mode=selected_mode, probability_calibrated=active.calibrated, timings_ms={"inference": round((predicted-start)*1000, 3), "explanation": round((explained-predicted)*1000, 3), "total": round((explained-start)*1000, 3)})
        except Exception:
            logger.exception("Provider response violates API contract")
            return error(500, "INVALID_MODEL_RESPONSE", "The model output does not match the agreed API contract.")

    return app


app = create_app()
