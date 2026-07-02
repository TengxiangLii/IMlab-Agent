# IMLab-Agent — agent instructions

Claude Code and Codex plugin for the IMLab `im` cluster (Institute of Science
Tokyo): two MCP servers (`imlab-hpc` for Slurm, `imlab-docs` for documentation
RAG) plus skills. See README.md for the user-facing overview.

`im` is a small **CPU-first** Slurm cluster: three AMD EPYC nodes (im1/im2/im3,
no GPUs) used for MPI/OpenMP computational chemistry. There is **no GPU, no
container runtime, and no enforced accounting** — treat jobs as CPU/MPI, free to
run, described in nodes/ranks/threads.

## Design rules (read before changing code)

- **The `imlab-hpc` tool surface mirrors the IRI Facility API** (DOE standard).
  The reference spec is **not committed** (ALCF's, no redistribution license);
  fetch when needed — `curl -s https://api.alcf.anl.gov/openapi.json -o openapi.json`
  (git-ignored). Before adding/renaming/removing a tool, check `IRI_CHECKLIST.md`
  and keep it in sync. Extensions with no IRI counterpart (like
  `run_command_on_cluster`) are allowed but must be marked as such. Coverage
  verdicts are **machine-specific** (here, allocations/GPU/containers are N/A);
  see PORTING.md.
- **All cluster interaction goes through `server/imlab_mcp/middleware.py`**
  (`run_command` / `write_remote_file`). Never shell out to ssh directly. It
  enforces: commands run under a **login shell**, the working dir is **$HOME**,
  and payloads travel **base64-encoded**. Output capped at 200KB. The macOS
  rsync-2.6.9 shim lives here too (remotemanager's default rsync transport
  version-checks at construction; stock macOS rsync is too old, and we only use
  direct SSH, so the check is relaxed).
- **Never write to stdout in server code** — the MCP stdio transport uses it for
  JSON-RPC. Log to stderr; remotemanager progress is redirected by middleware.
- **Tools are thin verbs; workflow knowledge lives in `plugins/imlab/skills/`.**
- **The MCP runtime must be self-contained under `server/`.** `plugins/imlab/
  .mcp.json` launches via `uv tool run --from git+https://…@main#subdirectory=server`.
  Do not depend on client plugin-root variables or repo-root `data/` at runtime;
  runtime files are package data under `server/imlab_mcp/data/`.
- **`models.py` is PSI/J-shaped, CPU-only.** ResourceSpec is node/ntasks/cpus +
  memory (no GPU field). No Container. Deviations at the bottom of
  `IRI_CHECKLIST.md`.
- Bias to simple. No new runtime deps without a strong reason (current: mcp,
  remotemanager, httpx, numpy). Python ≥ 3.10.

## Cluster facts

- SSH from `~/.imlab/config.json` (`ssh.host`, default alias `imlab`) →
  `131.112.104.58` (im1). Direct on-campus; off-campus via a `ProxyJump` through
  the TSUBAME login node (set in `~/.ssh/config`; the agent just uses the alias).
  Key-based auth only.
- Scheduler **Slurm 24.05** (sbatch/squeue/sacct/scancel/sinfo). Nodes AMD EPYC
  7713 (128 cores im1/im3, 64 im2); build with GNU + OpenMPI (`module load
  openmpi/5.0.7`).
- **No `--account` required** — `AccountingStorageEnforce=none`. `default_account`
  returns a value only if the user configured one; otherwise none is emitted.
- Partitions: `main` (default), `long`, `huge`, `debug` — all unlimited wall time.
  Default `duration` 1h so jobs schedule predictably.
- Storage: `/home` (500 GB), `/data` (9.1 TB). xfs, not Lustre; no scratch tier.
- **No GPUs, no containers** — never emit a GPU flag or a singularity/apptainer
  wrapper.

## Documentation search (RAG)

Source is **`server/imlab_mcp/data/imlab_guide.md`** — an *original* guide (facts
in our own words). It omits generic HPC background and anything queryable live
(`sinfo`/`sacct`/`module avail`); keep it that way. `rag/ingest.py` chunks by
markdown heading into `data/docs_index/chunks.json` (also the BM25 corpus),
committed as package data.

Search is **BM25 by default** (`EMBED_BASE_URL`/`EMBED_MODEL` empty). To enable
semantic search, set those to a reachable endpoint + model, set an API key, and
rebuild: `python -m imlab_mcp.rag.ingest`. Rebuild BM25-only after editing the
guide: `python -m imlab_mcp.rag.ingest --no-embed` (commit `chunks.json`).

## Development workflow

```bash
cd server
python3 -m venv .venv && .venv/bin/pip install -e .   # or just use ./run.sh
./run.sh imlab_mcp.doctor              # validate config, SSH, Slurm, index
.venv/bin/python tests/smoke.py        # live read-only test over MCP stdio
.venv/bin/python tests/smoke.py --job  # + submits a tiny real MPI job (free)
.venv/bin/python -m imlab_mcp.rag.ingest --no-embed  # rebuild docs index
```

- Validate the install-path runtime with `uv tool run --no-cache --from ./server
  imlab-doctor` (the `--no-cache` avoids uv reusing a stale local build).
- User settings live in `~/.imlab/config.json`. The `imlab-configuring` skill
  documents the schema.

## Repository map

```
.claude-plugin/         Claude Code marketplace manifest
.agents/plugins/        Codex marketplace manifest
plugins/imlab/          plugin payload for both clients
  .claude-plugin/  .codex-plugin/  .mcp.json  skills/
IRI_CHECKLIST.md        API coverage tracker — keep in sync with hpc_server.py
server/imlab_mcp/
  data/                 packaged guide, static facts, docs_index
  middleware.py         SSH layer (+ rsync shim) — the only place that talks to the cluster
  models.py             PSI/J schemas (CPU-only) + Slurm state normalization
  compute.py            JobSpec → sbatch, sacct/squeue parsing
  hpc_server.py         imlab-hpc MCP tools (IRI-grouped)
  docs_server.py        imlab-docs MCP tools
  rag/                  embed client / index store / markdown ingest
  doctor.py             health checks (python -m imlab_mcp.doctor)
  serving.py            shared CLI entry point
```

Skill names are machine-prefixed so this and sibling plugins (e.g. Tsubame4Agent)
can be installed at once without collisions.
