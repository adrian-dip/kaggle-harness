# ADR 0001 — System Architecture

**Status:** Accepted
**Date:** 2026-05-12

## Context

We want a local-first Kaggle harness that:

1. Exposes the Kaggle API over HTTP on `localhost` so other tools (scripts, IDE agents, web UIs) can drive it uniformly.
2. Runs ML experiments as isolated jobs against a pool of locally-networked machines (currently two).
3. Promotes a job's output artifact to a Kaggle competition submission and tracks the resulting score.
4. Tracks every run in MLflow (params, metrics, artifacts, leaderboard score).
5. Gives users a clean, declarative interface for submitting a script + its env without learning a harness-specific SDK.

The deployment target is a small fleet (≤ ~5 machines) reachable over Tailscale. One user or a small team.

## Decision

Build a three-tier system with one control plane and N stateless workers, using boring infra picked per its fit to this scale:

- **Gateway** — FastAPI app exposing all HTTP routes (Kaggle proxy + experiments + submissions + worker protocol).
- **Job queue** — Postgres `jobs` table claimed with `SELECT … FOR UPDATE SKIP LOCKED`. No Redis/RQ/Celery.
- **Bundle + artifact store** — MinIO (S3-compatible). Used by MLflow too.
- **Tracking** — MLflow server, Postgres backend (same DB, separate schema), MinIO artifact store.
- **Workers** — thin Python agents (one process per machine), poll the gateway, run jobs inside Docker, stream logs and artifacts back.
- **Networking** — Tailscale. Workers dial out only; no inbound ports on worker boxes.

Submitted scripts are packaged as **bundles**: a directory with an `experiment.yaml` manifest, an entrypoint, and optional `requirements.txt`. The manifest declares Kaggle inputs, outputs, resource needs, MLflow experiment, and an optional auto-submit. Inside the container, `/data` holds inputs (read-only), `/workspace` holds the bundle, `/out` collects artifacts.

## Options considered

### A. Ray (Ray Jobs API)

Ray Jobs is the closest semantic match to "submit a script to a cluster." It collapses scheduling, log streaming, GPU constraints, and dashboard to ~zero code.

- **Rejected because** Ray's real value is *distributed Python* (shared object store, `@ray.remote`, actors) — none of which we need. Our jobs are independent scripts. For 2 workers and a FIFO queue with labels, Ray is a heavy runtime dep on every worker plus an opinionated programming model the user scripts have to live inside (or escape via Docker, defeating the point). Debuggability also suffers — failures route through Ray internals rather than our own code.

### B. Nomad

Real scheduler, single binary, native Docker driver, language-agnostic, robust health/restart story.

- **Rejected because** all our workloads are Python ML scripts, so Nomad's language-agnostic generality is unused. The job-spec layer is overhead for two machines. Reasonable choice if we ever add non-Python workloads or grow past ~5 workers.

### C. Custom dispatcher on Postgres + MinIO (chosen)

Postgres jobs table + `SKIP LOCKED` claims + a ~200-LOC worker script. Every component does one obvious thing; failures are debugged in Python and SQL.

- **Chosen because** it is the smallest system that satisfies the requirements, uses infra MLflow needs anyway (Postgres + MinIO), and has zero framework opinions leaking into user scripts.

### Other rejected pieces

- **Redis/RQ for the queue.** Adds a service we don't otherwise need. Postgres + `SKIP LOCKED` is enough at this scale and gives us transactional state changes for free.
- **Celery.** Overkill; oriented at web-app task queues, not long ML jobs.
- **Kubernetes.** Operational tax dwarfs the value at this scale.
- **Per-job conda/venv (no Docker).** Doable but weakens isolation and reproducibility. Docker is the default; a future `venv` executor is a clean extension if we want lighter jobs.

## Consequences

**Positive**
- Small surface area. The whole "scheduler" is one SQL statement plus a sweeper for stale heartbeats.
- Workers are stateless and replaceable. Adding a third machine is `docker run kaggle-harness-worker`.
- Kaggle credentials live only on the gateway. Workers never see them.
- MLflow integration is conventional — user scripts call `mlflow.log_*` directly; no harness SDK.
- The bundle format is the stable user contract; we can swap the execution substrate later without breaking it.

**Negative / accepted trade-offs**
- We own scheduling (constraints, retries, requeue-on-death). Mitigated by keeping the surface intentionally small and the queries explicit.
- No bin-packing or cluster-wide optimisation. Acceptable at 2–5 workers.
- Distributed *training* across nodes is out of scope. If a single experiment needs it, the script handles it inside one worker (e.g. `torch.distributed` on a multi-GPU box).
- Gateway is a single point of failure. Acceptable for a local harness; recovery is restarting the process.

**Reversibility**
- Swapping the execution substrate (to Ray or Nomad) only touches the worker package + one service in the gateway. The bundle format, MLflow integration, and HTTP surface are insulated from the choice.

## Non-goals (explicit)

- Multi-tenant auth, RBAC, audit logging.
- High availability of the gateway.
- Autoscaling worker pools.
- Hyperparameter sweep orchestration (use a script + MLflow for now).
- Distributed training as a first-class harness feature.
