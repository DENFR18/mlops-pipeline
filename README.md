# MLOps Pipeline

Mini pipeline MLOps industrialisé from scratch : entraînement, tracking, serving et CI/CD.

## Stack

| Composant | Technologie |
|-----------|-------------|
| Modèle | Scikit-learn (Random Forest) |
| Tracking | MLflow |
| Serving | FastAPI |
| Containerisation | Docker |
| CI/CD | GitHub Actions |

## Architecture

```
src/train.py       → Entraînement du modèle + logging MLflow
src/predict.py     → API REST FastAPI pour servir les prédictions
tests/             → Tests automatisés (model + API)
.github/workflows/ → Pipeline CI/CD (lint → test → build Docker)
```

## Pipeline CI/CD

```
push → Lint (flake8) → Tests (pytest) → Build Docker image → Health check
```

## Lancement local

**1. Installer les dépendances**
```bash
pip install -r requirements.txt
```

**2. Entraîner le modèle**
```bash
python src/train.py
```

**3. Lancer l'API**
```bash
uvicorn src.predict:app --reload
```

**4. Tester l'API**
```powershell
Invoke-RestMethod -Method POST -Uri "http://localhost:8000/predict" `
  -ContentType "application/json" `
  -Body '{"sepal_length":5.1,"sepal_width":3.5,"petal_length":1.4,"petal_width":0.2}'
```

**5. Visualiser les expériences MLflow**
```bash
mlflow ui
# → http://127.0.0.1:5000
```

**6. Lancer avec Docker**
```bash
docker compose up --build
```

## Endpoints API

| Méthode | Route | Description |
|---------|-------|-------------|
| GET | `/health` | Statut de l'API |
| POST | `/predict` | Prédiction à partir de 4 features |

### Exemple de requête

```json
{
  "sepal_length": 5.1,
  "sepal_width": 3.5,
  "petal_length": 1.4,
  "petal_width": 0.2
}
```

### Exemple de réponse

```json
{
  "prediction": 0,
  "label": "setosa",
  "probabilities": [1.0, 0.0, 0.0]
}
```

## Résultats

| Métrique | Score |
|----------|-------|
| Accuracy | 1.00 |
| F1-score | 1.00 |
