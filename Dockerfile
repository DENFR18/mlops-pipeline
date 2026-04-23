FROM python:3.11-slim

WORKDIR /app

# Patch OS-level CVEs in the base image and create a non-root runtime user.
RUN apt-get update && apt-get upgrade -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system app && useradd --system --gid app --home /app --shell /sbin/nologin app

COPY --chown=app:app requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=app:app src/ ./src/
COPY --chown=app:app model/ ./model/

ENV MODEL_PATH=model/classifier.joblib

EXPOSE 8000
USER app

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/health').status==200 else 1)"

CMD ["uvicorn", "src.predict:app", "--host", "0.0.0.0", "--port", "8000"]
