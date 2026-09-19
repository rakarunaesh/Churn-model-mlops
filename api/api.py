"""FastAPI inference server for churn prediction"""
import os
import pickle
from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd
import joblib

app = FastAPI()

# Path overridable so the same image works whether the model is baked in
# (local testing) or fetched from S3 into a mounted volume (KServe on EKS).
MODEL_DIR = os.environ.get("MODEL_DIR", "models/trained")
MODEL_PATH = os.path.join(MODEL_DIR, os.environ.get("MODEL_FILENAME", "churn_model.pkl"))
PREPROCESSOR_PATH = os.path.join(MODEL_DIR, os.environ.get("PREPROCESSOR_FILENAME", "preprocessor.pkl"))

with open(MODEL_PATH, 'rb') as f:
    model = pickle.load(f)

preprocessor = joblib.load(PREPROCESSOR_PATH)


class CustomerData(BaseModel):
    gender: str
    SeniorCitizen: int
    Partner: str
    Dependents: str
    tenure: int
    PhoneService: str
    MultipleLines: str
    InternetService: str
    OnlineSecurity: str
    OnlineBackup: str
    DeviceProtection: str
    TechSupport: str
    StreamingTV: str
    StreamingMovies: str
    Contract: str
    PaperlessBilling: str
    PaymentMethod: str
    MonthlyCharges: float
    TotalCharges: float


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/predict")
def predict(data: CustomerData):
    # Same preprocessor fit in engineer.py - selects columns by name, so
    # order here doesn't matter, only that every training column is present.
    row = pd.DataFrame([data.dict()])
    features = preprocessor.transform(row)

    prediction = model.predict(features)[0]
    probability = model.predict_proba(features)[0][1]

    return {
        "churn": int(prediction),
        "churn_probability": float(probability)
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
