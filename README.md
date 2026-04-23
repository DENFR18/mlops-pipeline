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
terraform/         → Infra AWS (ECR + S3 artefacts MLflow)
.github/workflows/ → Pipeline CI/CD avec gates de sécurité
```

## Pipeline CI/CD

```
push/PR
  └─ lint (flake8)
      └─ test (pytest + couverture)
          ├─ checkov  ───┐
          ├─ sonarcloud  ├─> push GHCR (main seulement)
          └─ build ─ trivy ┘
```

- **Principe** : toute PR passe par lint + tests + trois scans de sécurité avant que l'image Docker ne puisse être poussée sur GHCR.
- **Concurrency group** : un nouveau commit sur une PR annule les runs précédents pour économiser les minutes CI.
- **Permissions least-privilege** : le workflow démarre en `contents: read` ; chaque job opt-in aux scopes dont il a besoin (`security-events: write` pour l'upload SARIF, `packages: write` pour le push GHCR).

## Sécurité

| Gate | Outil | Mode | Sortie |
|------|-------|------|--------|
| Container CVE | Trivy | Report (CRITICAL/HIGH, fixables) | SARIF → onglet Security |
| IaC misconfig | Checkov | Report (Dockerfile + Terraform) | SARIF → onglet Security |
| SAST + qualité | SonarCloud | Report (QG n'est pas blocking) | Analyse SonarCloud |

**Politique actuelle** : les trois scans sont en *report mode* le temps de trier la baseline CVE du base image Python. Tous les findings remontent dans l'onglet Security de GitHub via SARIF. Étape suivante : `.trivyignore` + `.checkov.yaml` pour figer les exceptions, puis flipper Trivy/Checkov en `exit-code: 1` / `soft_fail: false`.

**Hardening runtime** :
- Image Docker tourne sous un utilisateur non-root (`app:app`) avec `HEALTHCHECK`.
- `predict.py` restreint le chargement du modèle à `MODEL_DIR` via `Path.resolve()` (anti path-traversal / symlink escape), puisque `joblib.load` désérialise du pickle.
- `apt-get upgrade` dans le Dockerfile pour patcher les CVE OS du base image au moment du build.

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
