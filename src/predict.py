from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import joblib
import numpy as np
import os

app = FastAPI(title="Iris Classifier API", version="1.0.0")

MODEL_PATH = os.getenv("MODEL_PATH", "model/classifier.joblib")
LABELS = {0: "setosa", 1: "versicolor", 2: "virginica"}

model = joblib.load(MODEL_PATH) if os.path.exists(MODEL_PATH) else None


class PredictRequest(BaseModel):
    sepal_length: float
    sepal_width: float
    petal_length: float
    petal_width: float


class PredictResponse(BaseModel):
    prediction: int
    label: str
    probabilities: list[float]


@app.get("/health")
def health():
    return {"status": "ok", "model_loaded": model is not None}


@app.post("/predict", response_model=PredictResponse)
def predict(request: PredictRequest):
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    features = np.array([[
        request.sepal_length,
        request.sepal_width,
        request.petal_length,
        request.petal_width,
    ]])

    prediction = int(model.predict(features)[0])
    probabilities = model.predict_proba(features)[0].tolist()

    return PredictResponse(
        prediction=prediction,
        label=LABELS[prediction],
        probabilities=probabilities,
    )
