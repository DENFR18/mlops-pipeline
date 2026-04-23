from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import joblib
import numpy as np
import os
from pathlib import Path

app = FastAPI(title="Iris Classifier API", version="1.0.0")

# joblib.load unpickles arbitrary Python objects, so the model file must come
# from a trusted location. We pin loading to MODEL_DIR and reject any
# MODEL_PATH that resolves outside of it (path traversal, symlink escape).
MODEL_DIR = Path(os.getenv("MODEL_DIR", "model")).resolve()
_requested = Path(os.getenv("MODEL_PATH", "model/classifier.joblib")).resolve()

if not _requested.is_relative_to(MODEL_DIR):
    raise RuntimeError(
        f"MODEL_PATH {_requested} is outside trusted MODEL_DIR {MODEL_DIR}"
    )

MODEL_PATH = _requested
LABELS = {0: "setosa", 1: "versicolor", 2: "virginica"}

model = joblib.load(MODEL_PATH) if MODEL_PATH.exists() else None


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
