import pytest
from fastapi.testclient import TestClient
import joblib
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from train import train


@pytest.fixture(scope="session", autouse=True)
def trained_model():
    train()


def test_model_saved():
    assert os.path.exists("model/classifier.joblib")


def test_model_predicts():
    model = joblib.load("model/classifier.joblib")
    import numpy as np
    X = np.array([[5.1, 3.5, 1.4, 0.2]])
    pred = model.predict(X)
    assert pred[0] in [0, 1, 2]


def test_api_health():
    from predict import app
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_api_predict():
    from predict import app
    client = TestClient(app)
    payload = {
        "sepal_length": 5.1,
        "sepal_width": 3.5,
        "petal_length": 1.4,
        "petal_width": 0.2,
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "label" in data
    assert data["label"] in ["setosa", "versicolor", "virginica"]
