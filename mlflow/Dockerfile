FROM python:3.11-slim

RUN apt-get update && apt-get upgrade -y --no-install-recommends \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    mlflow==2.14.3 \
    psycopg2-binary==2.9.9 \
    boto3==1.34.131

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -fsS http://localhost:5000/ || exit 1

# Command uses env vars so the same image works across environments.
# Expected:
#   MLFLOW_BACKEND_STORE_URI     = postgresql://... (Neon)
#   MLFLOW_ARTIFACTS_DESTINATION = s3://<bucket>/ (Scaleway Object Storage)
#   MLFLOW_S3_ENDPOINT_URL       = https://s3.fr-par.scw.cloud
#   AWS_ACCESS_KEY_ID            = <SCW_ACCESS_KEY>
#   AWS_SECRET_ACCESS_KEY        = <SCW_SECRET_KEY>
CMD mlflow server \
    --host 0.0.0.0 \
    --port 5000 \
    --backend-store-uri "$MLFLOW_BACKEND_STORE_URI" \
    --artifacts-destination "$MLFLOW_ARTIFACTS_DESTINATION" \
    --serve-artifacts
