# Implementation Plan

Companion to `docs/adr/0001-system-architecture.md`. Read the ADR first.

This document is a contract for the coding agent. Follow it literally. If you find yourself wanting to deviate, stop and surface the disagreement instead of inventing structure.

---

## Guiding principles (read before writing any code)

These exist to prevent the usual failure mode: a "clean" architecture that grows a `managers/`, `helpers/`, `utils/`, `core/`, and three layers of indirection no one asked for.

1. **OOP where it earns its keep, not by default.**
   A class is justified when it owns state, has more than one method that uses that state, or has a swappable implementation. Otherwise a function is the right tool. Do not wrap every function in a class. Do not write `FooManager` / `FooHelper` / `FooUtils` — those names mean "I gave up on naming this." Find the noun or keep it as a function.

2. **Abstract base classes only for things that genuinely have ≥2 implementations, or that we mock in tests at the seam.**
   The seams that warrant ABCs: `JobRepository`, `BundleStore`, `ArtifactStore`, `Tracker`, `KaggleClient`, `Executor` (worker-side). Nothing else. Do not introduce an interface "for future flexibility." YAGNI.

3. **No premature plugin systems, no event buses, no DI container.**
   FastAPI's `Depends` is the DI container. Pydantic Settings is the config system. SQLAlchemy/SQLModel is the ORM. Don't reinvent these.

4. **Routes are thin.**
   A route handler does three things: parse the request, call **one** service method, return a response model. No business logic, no DB calls, no Kaggle calls in routes.

5. **Services orchestrate; they do not perform I/O directly.**
   `ExperimentService` calls `JobRepository`, `BundleStore`, `Tracker`, `KaggleClient`. The service is plain Python; the I/O lives behind the ABCs. This is the seam that keeps tests fast and the code understandable.

6. **One bounded context per package.** `kaggle/`, `jobs/`, `bundles/`, `experiments/`, `submissions/`, `tracking/` each own their models, services, and adapters. **No cross-package imports between siblings** — they meet in `api/` (routes assemble services) and in service constructors (one service may take another service as a dep, fine).

7. **Gateway and worker share only the wire protocol.**
   The worker package must not import gateway internals. They share a tiny `protocol/` package with the Pydantic models of the HTTP contract. This is the one shared dep; do not grow it.

8. **No speculative generality.** Examples of things **not** to add unless asked:
   - A second database backend.
   - A CLI that mirrors every API route.
   - A web UI.
   - Async retries with exponential backoff *unless* a real failure mode requires it.
   - Metrics/telemetry beyond structured logs.

9. **Comments and docstrings.** Default to none. Write a one-liner only when the *why* is non-obvious. Do not document what well-named code already says.

10. **One way to do each thing.** If you find two patterns for the same job (two HTTP clients, two ways to read settings, two log formatters), delete one before moving on.

---

## Repo layout

```
kaggle_harness/
├── pyproject.toml
├── docker-compose.yml
├── README.md
├── docs/                                  (existing)
│   ├── adr/0001-system-architecture.md
│   ├── implementation.md                  (this file)
│   └── ...
├── deploy/
│   ├── gateway.Dockerfile
│   ├── worker.Dockerfile
│   └── runner-base.Dockerfile             default image jobs run inside
├── examples/
│   └── titanic-baseline/                  reference bundle
│       ├── experiment.yaml
│       ├── train.py
│       └── requirements.txt
├── src/
│   ├── kaggle_harness/                    gateway package
│   │   ├── __init__.py
│   │   ├── config.py                      Settings (pydantic-settings)
│   │   ├── logging.py                     structlog setup
│   │   ├── db/
│   │   │   ├── engine.py                  SQLAlchemy engine + session
│   │   │   └── migrations/                alembic
│   │   ├── protocol/                      shared with worker
│   │   │   ├── __init__.py
│   │   │   └── messages.py                Pydantic: ClaimRequest, JobAssignment, LogChunk, JobReport, …
│   │   ├── kaggle/
│   │   │   ├── client.py                  KaggleClient ABC + KaggleApiClient impl
│   │   │   └── service.py                 KaggleService (list/download/submit/poll)
│   │   ├── bundles/
│   │   │   ├── manifest.py                ExperimentManifest (pydantic, validated)
│   │   │   ├── bundle.py                  Bundle (zip in/out, manifest accessor)
│   │   │   └── store.py                   BundleStore ABC + MinioBundleStore
│   │   ├── jobs/
│   │   │   ├── models.py                  Job (SQLModel), JobStatus (enum)
│   │   │   ├── repository.py              JobRepository ABC + PostgresJobRepository
│   │   │   └── service.py                 JobService (claim, complete, fail, requeue_stale)
│   │   ├── tracking/
│   │   │   ├── tracker.py                 Tracker ABC + MlflowTracker
│   │   │   └── linkage.py                 helpers to tag runs with kaggle.* metadata
│   │   ├── experiments/
│   │   │   └── service.py                 ExperimentService (submit, status, cancel)
│   │   ├── submissions/
│   │   │   ├── service.py                 SubmissionService (promote artifact, poll)
│   │   │   └── poller.py                  background task: poll Kaggle until scored
│   │   └── api/
│   │       ├── app.py                     FastAPI factory, lifespan, routers
│   │       ├── deps.py                    Depends providers (Settings, services)
│   │       ├── errors.py                  exception handlers
│   │       └── routes/
│   │           ├── competitions.py
│   │           ├── datasets.py
│   │           ├── kernels.py
│   │           ├── experiments.py
│   │           ├── submissions.py
│   │           └── workers.py             register, claim, heartbeat, report, logs
│   └── kaggle_harness_worker/             worker package, separate distribution
│       ├── __init__.py
│       ├── config.py                      WorkerSettings
│       ├── agent.py                       Agent — main loop
│       ├── client.py                      GatewayClient (httpx) — uses protocol.messages
│       ├── executor.py                    Executor ABC + DockerExecutor
│       └── reporter.py                    LogReporter (streams stdout/stderr → gateway)
└── tests/
    ├── unit/                              fast, no I/O — service tests with fake ABC impls
    ├── integration/                       compose-up, hit real Postgres/MinIO/MLflow
    └── e2e/                               full flow: bundle → job → submission stub
```

### Hard rules about this tree

- A file's package determines what it can import. **Sibling packages do not import each other** under `kaggle_harness/`. The only places that compose services are `api/deps.py` and service constructors.
- `protocol/` contains **only** Pydantic models for HTTP messages. No business logic, no I/O. Both gateway and worker import from it.
- `db/migrations/` is the only place SQL DDL lives. No `CREATE TABLE IF NOT EXISTS` sprinkled in code.
- `kaggle_harness_worker` does **not** depend on `kaggle_harness` except via `kaggle_harness.protocol`. Enforced by import-linter or a unit test.

---

## Abstractions (the seams)

Each ABC below is justified: it has either >1 real implementation planned, or it is mocked in tests.

### `KaggleClient` (ABC)
Wraps the official `kaggle-api`. Sync internally; gateway calls via `run_in_threadpool`.

```python
class KaggleClient(ABC):
    @abstractmethod
    def competitions_list(self, search: str | None) -> list[Competition]: ...
    @abstractmethod
    def download_competition_files(self, slug: str, dest: Path) -> None: ...
    @abstractmethod
    def download_dataset_files(self, slug: str, dest: Path) -> None: ...
    @abstractmethod
    def submit(self, competition: str, file: Path, message: str) -> SubmissionRef: ...
    @abstractmethod
    def submissions(self, competition: str) -> list[SubmissionStatus]: ...
```

Impls: `KaggleApiClient` (real), `FakeKaggleClient` (tests).

### `BundleStore` (ABC)
Object storage for uploaded bundles.

```python
class BundleStore(ABC):
    @abstractmethod
    async def put(self, bundle_id: str, data: BinaryIO) -> None: ...
    @abstractmethod
    async def get(self, bundle_id: str) -> bytes: ...
    @abstractmethod
    async def signed_url(self, bundle_id: str, ttl: timedelta) -> str: ...
```

Impl: `MinioBundleStore`. Mock in tests.

### `ArtifactStore`
Same shape as `BundleStore`, different prefix. Implement as a thin subclass; **do not** generalise both into one "ObjectStore" until you need to.

### `Tracker` (ABC)
Experiment tracking.

```python
class Tracker(ABC):
    @abstractmethod
    def create_run(self, experiment: str, name: str) -> RunHandle: ...
    @abstractmethod
    def log_params(self, run_id: str, params: dict[str, Any]) -> None: ...
    @abstractmethod
    def log_metric(self, run_id: str, key: str, value: float, step: int | None) -> None: ...
    @abstractmethod
    def log_artifact(self, run_id: str, path: Path, artifact_path: str | None) -> None: ...
    @abstractmethod
    def set_tag(self, run_id: str, key: str, value: str) -> None: ...
```

Impl: `MlflowTracker`. The user script also talks MLflow directly via env vars — that's a separate code path and intentional.

### `JobRepository` (ABC)
The scheduler is hidden behind this.

```python
class JobRepository(ABC):
    @abstractmethod
    async def enqueue(self, job: Job) -> None: ...
    @abstractmethod
    async def claim_next(self, worker_id: str, caps: WorkerCapabilities) -> Job | None: ...
    @abstractmethod
    async def heartbeat(self, job_id: UUID, worker_id: str) -> None: ...
    @abstractmethod
    async def mark_succeeded(self, job_id: UUID, artifacts: list[ArtifactRef]) -> None: ...
    @abstractmethod
    async def mark_failed(self, job_id: UUID, reason: str) -> None: ...
    @abstractmethod
    async def requeue_stale(self, older_than: timedelta) -> int: ...
    @abstractmethod
    async def get(self, job_id: UUID) -> Job: ...
```

Impl: `PostgresJobRepository` using `FOR UPDATE SKIP LOCKED`.

### `Executor` (ABC, worker-side)
Runs a job. The interface is small on purpose.

```python
class Executor(ABC):
    @abstractmethod
    async def run(self, assignment: JobAssignment, on_log: Callable[[str], None]) -> ExecutionResult: ...
```

Impl: `DockerExecutor`. A future `VenvExecutor` is a possibility but **do not write it yet**.

### Services (concrete, no ABC)

These do not get ABCs — they are not swapped, and unit tests inject fake repositories/clients instead of faking the service.

- `KaggleService(KaggleClient)` — domain methods over the Kaggle client.
- `JobService(JobRepository)` — orchestrates job lifecycle from the gateway side.
- `ExperimentService(JobService, BundleStore, Tracker, KaggleService)` — the main use case: "submit an experiment."
- `SubmissionService(KaggleService, Tracker, ArtifactStore)` — promote and poll.

### Data classes

- `ExperimentManifest` — Pydantic, parses `experiment.yaml`, validates ids and resource limits.
- `Job` — SQLModel persisted row.
- `Bundle` — value object: id, manifest, blob ref.
- `JobAssignment` — what the gateway hands a worker (Pydantic, in `protocol/`).
- `WorkerCapabilities` — labels, gpu, cpu, memory (Pydantic, in `protocol/`).

---

## Data model (Postgres)

One schema, four tables. Migrations only via alembic.

```
jobs                    workers                experiments              submissions
─────                   ─────                  ─────                    ─────
id (uuid pk)            id (text pk)           id (uuid pk)             id (uuid pk)
experiment_id (fk)      labels (text[])        name (text)              experiment_id (fk)
bundle_id (text)        gpu (bool)             manifest (jsonb)         competition (text)
status (enum)           cpu (int)              mlflow_run_id (text)     kaggle_ref (text)
worker_id (fk nullable) memory_mb (int)        created_at               public_score (float)
requires (jsonb)        last_seen (timestamptz)                         private_score (float)
priority (int)                                                          status (enum)
created_at                                                              created_at
started_at
finished_at
heartbeat_at
error (text)
artifacts (jsonb)
```

`status` enums:
- jobs: `queued | running | succeeded | failed | cancelled`
- submissions: `pending | running | scored | failed`

**The claim query** lives in `PostgresJobRepository.claim_next`:

```sql
UPDATE jobs SET status='running', worker_id=:wid, started_at=now(), heartbeat_at=now()
WHERE id = (
  SELECT id FROM jobs
  WHERE status = 'queued'
    AND (requires->>'gpu' = 'false' OR :worker_has_gpu)
    AND (requires->'labels' IS NULL
         OR requires->'labels' <@ to_jsonb(:worker_labels::text[]))
  ORDER BY priority DESC, created_at ASC
  FOR UPDATE SKIP LOCKED
  LIMIT 1
)
RETURNING *;
```

This query is the entire scheduler. Do not abstract it into a "query builder."

---

## Worker protocol (HTTP)

All endpoints under `/workers`. Pydantic models live in `protocol/messages.py`.

| Method | Path                              | Purpose                                |
| ------ | --------------------------------- | -------------------------------------- |
| POST   | `/workers/register`               | announce self + capabilities → token   |
| POST   | `/workers/claim`                  | long-poll for next job (≤30s)          |
| POST   | `/workers/jobs/{id}/heartbeat`    | extend lease                           |
| POST   | `/workers/jobs/{id}/logs`         | append log chunk                       |
| POST   | `/workers/jobs/{id}/report`       | terminal report: artifacts + status    |
| GET    | `/workers/bundles/{id}`           | download bundle (or 307 to MinIO)      |
| POST   | `/workers/artifacts/{id}`         | upload artifact (or 307 to MinIO)      |

Auth: shared bearer token from gateway env, scoped to the worker on registration.

---

## Bundle contract

A bundle is a zip with `experiment.yaml` at the root. The manifest is the **only** thing the harness reads — everything else is opaque to it.

```yaml
name: titanic-xgb-v3            # required, slug-safe
entrypoint: python train.py     # required, shell-exec'd inside the container
runtime:
  image: runner-base:py311      # default; user can override
  requirements: requirements.txt  # optional, installed at container start
resources:
  cpu: 4
  memory: 8G
  gpu: false                    # or true; routed by JobRepository
  labels: []                    # require specific worker labels
inputs:
  competitions: [titanic]       # → /data/competitions/titanic/
  datasets: [uciml/iris]        # → /data/datasets/uciml__iris/
outputs:                        # collected from /out/ on success
  - submission.csv
  - model.pkl
env:                            # passed into the container
  SEED: "42"
mlflow:
  experiment: titanic-baseline
submit:                         # optional: auto-submit after success
  competition: titanic
  file: submission.csv
  message: "{name}"
```

In-container contract (do not change):

- `/workspace` — read-only mount of the bundle.
- `/data` — read-only mount of staged Kaggle inputs.
- `/out` — read-write scratch; artifacts collected from here.
- env: `MLFLOW_TRACKING_URI`, `MLFLOW_RUN_ID`, `MLFLOW_EXPERIMENT_NAME`, plus user `env:`.

---

## Phased implementation

Each phase is independently mergeable and leaves the tree in a working state. Do not start a phase before the previous one is reviewed.

### Phase 1 — Skeleton + Kaggle proxy
- `config.py`, `logging.py`, `db/engine.py`, alembic init.
- `KaggleClient` + `KaggleApiClient` + `KaggleService`.
- `api/app.py`, routes for `/competitions`, `/datasets`, `/kernels` (read-only ops only).
- `docker-compose.yml` with `gateway`, `postgres`, `minio`, `mlflow`.
- One pytest that hits `/competitions` against a fake `KaggleClient`.

**Done when:** `curl localhost:8000/competitions?search=titanic` returns real data.

### Phase 2 — Bundles + jobs table
- `ExperimentManifest` + tests.
- `BundleStore` ABC + `MinioBundleStore`.
- `Job` model, alembic migration, `JobRepository` ABC + `PostgresJobRepository` (with the claim query).
- `JobService.requeue_stale` background task in the gateway lifespan.
- No execution yet; jobs sit in `queued` forever.

**Done when:** `POST /experiments` accepts a zip, stores it, creates a `queued` job; `GET /experiments/{id}` returns it.

### Phase 3 — Worker MVP
- `kaggle_harness_worker` package.
- `Agent` loop: register → claim (long poll) → run → report.
- `DockerExecutor`: pulls bundle, mounts `/workspace`, `/data` (stub for now), `/out`, runs entrypoint, captures logs.
- `LogReporter` posts log chunks to the gateway.
- Gateway worker routes implemented.

**Done when:** running the worker on a second machine consumes a queued job end-to-end and reports `succeeded`.

### Phase 4 — Inputs staging
- Gateway resolves `inputs:` before assignment: downloads competition/dataset files via `KaggleService` into MinIO under `inputs/<hash>/`.
- Worker downloads them into `/data` before container start.
- Cache key on `(slug, version)` so the same dataset is not re-fetched.

**Done when:** the example `titanic-baseline` bundle trains against real Titanic data on a worker.

### Phase 5 — MLflow integration
- `Tracker` + `MlflowTracker`.
- Gateway creates the MLflow run *before* enqueue; passes `run_id` to the worker; worker injects env into the container.
- Declared `outputs:` auto-logged as MLflow artifacts on success.

**Done when:** every completed job has an MLflow run with params, metrics (whatever the script logged), and artifacts.

### Phase 6 — Submissions
- `SubmissionService.promote(experiment_id, file)` uploads artifact via `KaggleService`.
- `submissions/poller.py` background task: polls Kaggle every 30s until scored, tags the MLflow run with `kaggle.public_score` / `kaggle.private_score`.
- Auto-submit honoured if `submit:` is present in the manifest.

**Done when:** a bundle with `submit:` lands a real score on a real (test) competition, visible in MLflow.

### Phase 7 — Polish (optional, only after the above is real)
- `/experiments/{id}/logs` SSE stream.
- Worker labels + `requires.labels` end-to-end test.
- Cancellation (`POST /experiments/{id}/cancel`).
- README + one-page user guide.

---

## What the coding agent must not do

These are the predictable failure modes. Resist them.

- **Do not** add a service registry, dependency-injection framework, or plugin loader. FastAPI `Depends` is sufficient.
- **Do not** generalise `BundleStore` and `ArtifactStore` into a polymorphic `ObjectStore` "for symmetry." Two thin classes are clearer.
- **Do not** introduce a second async runtime, message bus, or background worker library. The poller and stale-requeue tasks run as `asyncio` tasks in the gateway lifespan. That is enough.
- **Do not** write a CLI that mirrors the HTTP API. The HTTP API *is* the interface. If a CLI is wanted later it lives in its own package and consumes the API.
- **Do not** add abstract "BaseService" / "BaseEntity" / "BaseRepository" classes. Each service and entity is concrete and named after what it does.
- **Do not** add retry/backoff/circuit-breaker libraries before a real failure mode demands them. The worker's claim loop is a plain `while True: sleep(1) on empty`.
- **Do not** import across sibling packages under `kaggle_harness/`. If you feel the urge, surface it — the abstraction is probably misplaced.
- **Do not** write multi-paragraph docstrings or comments narrating what the code does.

If the plan is wrong, say so before deviating. A clear "this won't work because X" is welcome. A silent reinterpretation is not.
