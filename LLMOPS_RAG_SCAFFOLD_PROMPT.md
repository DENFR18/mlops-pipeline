# Prompt de scaffolding — `llmops-rag-pipeline`

> Copie/colle ce fichier comme **premier message** dans une session Claude Code locale lancée depuis le dossier `llmops-rag-pipeline` cloné.

---

## Contexte à donner à Claude

Je veux que tu scaffoldes un projet **LLMOps de qualité production** appelé `llmops-rag-pipeline`.

C'est le pendant LLM de mon projet précédent `mlops-pipeline` (https://github.com/DENFR18/mlops-pipeline). Réutilise les mêmes patterns DevSecOps (Sonar, Trivy, Checkov, gating CI), la même rigueur de CI/CD (GitHub Actions), et le même cloud cible (Scaleway Serverless Containers + Neon Postgres). Le narratif LinkedIn sera : *"j'ai appliqué les principes MLOps à un agent LLM avec RAG"*.

Pas de code "demo jouet" — je veux un truc qu'un recruteur SRE/MLOps senior puisse cloner, lancer, et auditer.

## Stack imposée

| Couche | Techno |
|---|---|
| LLM | Claude API (modèle `claude-sonnet-4-6`), avec **prompt caching activé** |
| RAG vector store | pgvector sur Neon Postgres (réutilise mon compte Neon existant) |
| Framework RAG | LlamaIndex (préféré à LangChain pour la stabilité d'API) |
| Embeddings | `voyage-3` (Voyage AI) ou fallback `text-embedding-3-small` (OpenAI) |
| API serving | FastAPI + Uvicorn, streaming SSE pour les réponses |
| Observabilité LLM | Langfuse (self-hosted Docker compose pour le dev, cloud pour la prod) |
| Eval-as-code | Promptfoo + Ragas (faithfulness, answer_relevancy, context_precision) |
| Sécu prompt | LLM Guard (prompt injection scanner + PII redaction) |
| Containerisation | Docker, Docker Compose |
| Runtime cloud | Scaleway Serverless Containers |
| Registry | GHCR + Scaleway Container Registry |
| IaC | Terraform (Neon db + Scaleway namespaces) |
| CI/CD | GitHub Actions |
| Sécu CI | flake8, pytest+coverage, **SonarCloud**, **Trivy** (image), **Checkov** (Dockerfile + Terraform), SARIF upload vers GitHub Security |

## Structure attendue

```
llmops-rag-pipeline/
├── README.md                      # Voir section "README" ci-dessous
├── Dockerfile                      # API multi-stage, non-root user, healthcheck
├── docker-compose.yml              # Stack locale : api + postgres+pgvector + langfuse
├── requirements.txt
├── pyproject.toml                  # ruff + pytest config
├── sonar-project.properties
├── .gitignore
├── .env.example                    # Toutes les vars sans valeurs
├── src/
│   ├── __init__.py
│   ├── config.py                   # Pydantic Settings, lit env
│   ├── ingest.py                   # Pipeline d'ingestion : load → chunk → embed → upsert pgvector
│   ├── rag.py                      # Retriever + reranker, query pgvector
│   ├── llm.py                      # Wrapper Claude API avec prompt caching
│   ├── guards.py                   # LLM Guard : injection + PII
│   ├── tracing.py                  # Init Langfuse + decorators
│   └── api.py                      # FastAPI : /health /ingest /query (SSE) /eval
├── data/
│   └── sample_docs/                # Quelques .md pour démo (docs Anthropic ou tes propres notes)
├── tests/
│   ├── test_chunking.py
│   ├── test_retrieval.py
│   ├── test_guards.py              # Tests anti-prompt-injection
│   └── test_api.py
├── evals/
│   ├── promptfooconfig.yaml        # Eval Promptfoo (assertions, gradients)
│   ├── ragas_eval.py               # Eval sémantique Ragas
│   └── golden_dataset.jsonl        # 30-50 paires (question, réponse_attendue, contexte)
├── terraform/
│   ├── main.tf                     # Provider Scaleway + Neon
│   ├── neon.tf                     # Database + extension pgvector
│   ├── scaleway.tf                 # Registry + Serverless namespace
│   └── variables.tf
├── .github/
│   └── workflows/
│       ├── ci.yml                  # Lint → test → sonar → build → trivy → checkov → push GHCR
│       ├── eval.yml                # Run Ragas + Promptfoo, gate sur seuils
│       ├── deploy-scaleway.yml     # Provision + deploy
│       └── destroy-scaleway.yml    # Teardown on-demand
└── docs/
    ├── architecture.md             # Diagramme ASCII détaillé
    └── llmops-vs-mlops.md          # Le narratif comparatif (réutilisable pour LinkedIn)
```

## Détails non négociables

### 1. Prompt caching Claude
Dans `src/llm.py`, **active explicitement le cache Anthropic** sur le system prompt + le contexte RAG retrieved (`cache_control: {"type": "ephemeral"}`). Documente le hit rate attendu dans le README. C'est un gros différenciateur vs un usage naïf.

### 2. Streaming SSE
L'endpoint `/query` doit streamer la réponse en SSE (Server-Sent Events). Pas de réponse bloquante.

### 3. Eval comme gate CI
Le workflow `eval.yml` doit :
- Tourner Ragas sur le `golden_dataset.jsonl`
- **Échouer si** : faithfulness < 0.85 OU answer_relevancy < 0.80 OU context_precision < 0.75
- Poster un commentaire sur la PR avec le tableau des métriques (avant/après)

### 4. Sécu prompt
`src/guards.py` doit bloquer en amont :
- Prompt injection (LLM Guard `PromptInjection` scanner)
- PII en sortie (LLM Guard `Anonymize`)
- Tests unitaires avec ≥ 10 prompts d'attaque connus (jailbreaks classiques)

### 5. Observabilité
Chaque appel LLM doit être tracé dans Langfuse avec :
- Prompt complet + réponse
- Coût en tokens (input/output/cache_read/cache_write)
- Latence
- Score d'eval si dispo
- User_id + session_id

### 6. CI/CD réplique de mlops-pipeline
Reprends **à l'identique** le pattern de `ci.yml` du repo `mlops-pipeline` :
- Job `lint` (flake8/ruff)
- Job `test` (pytest --cov)
- Job `sonar` (SonarCloud)
- Job `build` (Docker buildx)
- Job `trivy` (scan image, SARIF)
- Job `checkov` (scan Dockerfile + Terraform, SARIF)
- Job `push-ghcr` gated par tous les précédents, sur `main` only

### 7. README
Le README doit contenir, dans l'ordre :
1. Titre + badges (CI, Sonar, license)
2. **Une phrase d'accroche** qui positionne le projet comme la suite de mlops-pipeline
3. Diagramme ASCII de l'archi (style mlops-pipeline)
4. Tableau de stack
5. Section "**MLOps vs LLMOps : ce qui change**" (3-4 paragraphes — le matériel LinkedIn)
6. Quickstart local (`docker compose up`)
7. Section CI/CD avec tableau des jobs
8. Section "Eval-as-code" expliquant les seuils et la philosophie
9. Section déploiement Scaleway (calque sur mlops-pipeline)
10. Section "Limites assumées" honnête (pas de fine-tuning, pas de multi-tenant, etc.)

### 8. Secrets (juste documenter, pas committer)
Dans `.env.example` et le README, lister :
- `ANTHROPIC_API_KEY`
- `VOYAGE_API_KEY` (ou `OPENAI_API_KEY`)
- `NEON_DATABASE_URL`
- `LANGFUSE_PUBLIC_KEY` + `LANGFUSE_SECRET_KEY` + `LANGFUSE_HOST`
- `SCW_ACCESS_KEY`, `SCW_SECRET_KEY`, `SCW_DEFAULT_PROJECT_ID`, `SCW_DEFAULT_ORGANIZATION_ID`
- `SONAR_TOKEN`

## Ordre d'exécution recommandé

1. Init repo + structure de dossiers + .gitignore + pyproject.toml + requirements.txt
2. `src/config.py` + `src/llm.py` (avec prompt caching) + tests unitaires
3. `src/ingest.py` + `src/rag.py` + tests
4. `src/guards.py` + tests anti-injection
5. `src/tracing.py` + intégration Langfuse
6. `src/api.py` (FastAPI + SSE)
7. Dockerfile + docker-compose.yml
8. Terraform
9. Workflows GitHub Actions (ci.yml d'abord, puis eval.yml, puis deploy/destroy)
10. `evals/` (golden dataset + ragas + promptfoo)
11. README final
12. Premier commit + push sur `main`

## Branches & commits

- **Branche principale** : `main` (pas de préfixe imposé, on est en local)
- **Convention de commits** : Conventional Commits (`feat:`, `fix:`, `docs:`, `ci:`, `chore:`)
- **Pas de co-author Claude** dans les commits — j'utilise mes propres credentials git

## Ce que je ne veux PAS

- ❌ Pas de LangChain (instable, trop verbeux)
- ❌ Pas de framework "agent" (CrewAI, AutoGen) — c'est du RAG simple bien fait, pas un agent multi-step
- ❌ Pas de fine-tuning ni LoRA (hors-scope)
- ❌ Pas de Streamlit / Gradio en frontend — l'API FastAPI suffit
- ❌ Pas d'over-engineering : si un fichier fait 50 lignes, ne le découpe pas en 5 modules
- ❌ Pas de commentaires qui paraphrasent le code

---

## Une fois le scaffolding fait

Demande-moi :
1. De rédiger la section `docs/llmops-vs-mlops.md` (qui sera la base de mon post LinkedIn)
2. De créer un golden dataset de 30 questions sur la doc Anthropic Claude API
3. De setup le premier déploiement Scaleway end-to-end
