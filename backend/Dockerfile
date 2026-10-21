FROM python:3.14-slim
WORKDIR /app
COPY backend/requirements-verified.txt backend/requirements-verified.txt
COPY ml/requirements-verified.txt ml/requirements-verified.txt
RUN pip install --no-cache-dir -r backend/requirements-verified.txt -r ml/requirements-verified.txt
RUN pip install --no-cache-dir torch==2.14.1 --index-url https://download.pytorch.org/whl/cpu
COPY backend backend
COPY ml ml
ENV PYTHONPATH=ml:. PHISHX_MODE=model PHISHX_PROVIDER=ml.integration:create_provider PHISHX_MODEL_PATH=/models/classical.joblib PHISHX_RELEASE_PATH=/models
RUN useradd --uid 10001 --create-home app
USER app
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
