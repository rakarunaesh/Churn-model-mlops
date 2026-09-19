FROM python:3.11-slim

WORKDIR /app

# Build context is the repo root (see .github/workflows/mlops-pipeline.yaml),
# so paths below are root-relative, not relative to this Dockerfile.
COPY api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY api/api.py .
COPY models/trained/ models/trained/

EXPOSE 8000

CMD ["python", "api.py"]
