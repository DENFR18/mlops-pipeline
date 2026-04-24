# MLOps Pipeline

End-to-end MLOps lab déployé sur [Scaleway](https://www.scaleway.com) : entraînement, tracking persistant, serving, CI/CD sécurisé, deploy & teardown on-demand.

![CI](https://github.com/DENFR18/mlops-pipeline/actions/workflows/ci.yml/badge.svg)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=DENFR18_mlops-pipeline&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=DENFR18_mlops-pipeline)

## Architecture

```
┌─────────────────┐        ┌─────────────────────────────────────────────┐
│   GitHub Actions│        │                   Scaleway fr-par           │
│                 │        │                                             │
│  lint → test ──┐│        │  ┌──────────────┐     ┌──────────────┐      │
│                ││        │  │  mlops-api   │     │    mlflow    │      │
│  Sonar ────────┤│        │  │  (FastAPI)   │     │   tracking   │      │
│  Trivy ────────┤│──▶ SCR │  │   :8000      │     │    :5000     │      │
│  Checkov ──────┘│ (image)│  └──────────────┘     └──────┬───────┘      │
│        │        │        │                              │              │
│        ▼        │        │                              │ artifacts    │
│  deploy-scw ────┼──▶ scw │                              ▼              │
│  destroy-scw ───┼──▶ scw │                   ┌─────────────────────┐   │
└─────────────────┘        │                   │  Object Storage     │   │
                           │                   │  (S3-compatible)    │   │
                           └───────────────────┴─────────────────────┴───┘
                                                          │
                                        backend metadata  │
                                                ▼         │
                                        ┌─────────────────┴─┐
                                        │  Neon Postgres    │
                                        │  (free tier)      │
                                        └───────────────────┘
```

## Stack

| Couche | Techno |
|---|---|
| Modèle | scikit-learn (Random Forest, dataset Iris) |
| Training & tracking | MLflow 2.14 |
| Backend metadata MLflow | Neon Postgres |
| Artifact store | Scaleway Object Storage (S3-compatible) |
| Serving | FastAPI + Uvicorn |
| Containerisation | Docker, Docker Compose |
| Runtime cloud | Scaleway Serverless Containers |
| Container registry | Scaleway Container Registry + GHCR |
| IaC | Terraform (AWS targets existants) |
| CI/CD | GitHub Actions |
| Qualité & sécu | flake8, pytest, SonarCloud, Trivy, Checkov, SARIF upload |

## Structure

```
src/
  train.py          # Entraînement, log params/metrics/model to MLflow
  predict.py        # API FastAPI (/health, /predict)
tests/
  test_model.py     # Tests modèle + API
mlflow/
  Dockerfile        # Image du MLflow tracking server
Dockerfile          # Image de l'API
docker-compose.yml  # Stack locale (API + MLflow)
terraform/          # Infra AWS (ECR, S3, KMS)
.github/workflows/
  ci.yml                 # Lint, test, build, security scans, push GHCR
  deploy-scaleway.yml    # Provision registry/bucket + deploy API + MLflow
  destroy-scaleway.yml   # Teardown on-demand (toggles registry/bucket)
```

## CI/CD

| Job | Rôle |
|---|---|
| Lint | `flake8` sur `src/` et `tests/` |
| Test | `pytest` + coverage XML |
| Security · SonarCloud | SAST + Quality Gate |
| Security · Checkov (IaC) | Scan Dockerfile + Terraform, SARIF → GitHub Security |
| Build Docker Image | Train le modèle puis build + healthcheck |
| Security · Trivy (Docker) | Scan CVE de l'image, SARIF → GitHub Security |
| Push to GHCR | Push de l'image vers `ghcr.io/denfr18/mlops-pipeline` (main uniquement, gated par tous les scans) |

## Déploiement Scaleway

### Prérequis

GitHub Secrets à configurer dans le repo :

| Secret | Source |
|---|---|
| `SCW_ACCESS_KEY` | Scaleway IAM API key |
| `SCW_SECRET_KEY` | Idem (visible une seule fois à la création) |
| `SCW_DEFAULT_ORGANIZATION_ID` | Settings organisation Scaleway |
| `SCW_DEFAULT_PROJECT_ID` | Settings du projet Scaleway |
| `NEON_DATABASE_URL` | Connection string [Neon](https://neon.tech) (`postgresql://...?sslmode=require`) |
| `SONAR_TOKEN` | Token SonarCloud (si scan activé) |

### Deploy

Onglet **Actions** → **Deploy to Scaleway** → *Run workflow*.

Le workflow :
1. Installe le CLI Scaleway
2. Crée (ou réutilise) le bucket Object Storage pour les artifacts MLflow
3. Crée (ou réutilise) les namespaces Registry + Serverless Containers
4. Build & push l'image MLflow, deploy le container `mlflow` avec `NEON_DATABASE_URL` et credentials S3 en secret env vars
5. Attend que MLflow soit `ready` et récupère son URL publique
6. Entraîne le modèle avec `MLFLOW_TRACKING_URI` pointant sur le MLflow déployé → runs trackés dans Neon + artifacts dans S3
7. Build & push l'image API avec le modèle baké dedans
8. Deploy le container `mlops-api`
9. Écrit les 2 URLs (API + MLflow) dans le summary du run

### Destroy

Onglet **Actions** → **Destroy Scaleway deployment** → *Run workflow*.

Options :
- `delete_registry` : supprimer aussi le Container Registry (sinon gardé pour les futurs déploiements)
- `delete_bucket` : supprimer le bucket MLflow (⚠️ perd tous les artifacts)

Par défaut, les 2 sont à `false` → seuls les containers serverless sont détruits. Free tier respecté.

## Endpoints API

| Méthode | Route | Description |
|---|---|---|
| GET | `/health` | Statut + présence du modèle en mémoire |
| POST | `/predict` | Inférence à partir des 4 features Iris |
| GET | `/docs` | Swagger UI (généré par FastAPI) |

### Exemple

```bash
curl -X POST https://<api-url>/predict \
  -H "Content-Type: application/json" \
  -d '{"sepal_length":5.1,"sepal_width":3.5,"petal_length":1.4,"petal_width":0.2}'
```

Réponse :
```json
{"prediction": 0, "label": "setosa", "probabilities": [1.0, 0.0, 0.0]}
```

## Lancement local

```bash
# Install & train
pip install -r requirements.txt
python src/train.py

# Stack complète (API + MLflow)
docker compose up --build
# API     → http://localhost:8000
# Swagger → http://localhost:8000/docs
# MLflow  → http://localhost:5001
```

## Tests

```bash
pytest tests/ -v --cov=src
```

## Limites assumées

Ce projet est un **lab pédagogique** centré sur la chaîne MLOps, pas sur le modèle :
- Dataset Iris (toy), pas représentatif d'un cas d'usage réel
- Pas d'orchestrateur (Airflow / Prefect) — étape suivante prévue pour piloter ingestion → training → évaluation → promotion
- Pas de détection de drift / réentraînement automatique — à ajouter via Evidently AI ou équivalent
- Pas de feature store, pas d'A/B testing de modèles

L'accent est mis sur **l'industrialisation** : CI/CD sécurisé, déploiement cloud reproductible, tracking MLflow persistant, IaC.
