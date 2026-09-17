FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir fastapi uvicorn pydantic scikit-learn pandas joblib

COPY api.py .
COPY models/ models/

EXPOSE 8000

CMD ["python", "api.py"]
