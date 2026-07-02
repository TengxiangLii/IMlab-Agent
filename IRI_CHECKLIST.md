# IRI Facility API coverage checklist

Tracks how far `imlab-hpc` covers the [IRI Facility API](https://api.alcf.anl.gov/)
(ALCF implementation, spec at api.alcf.anl.gov/openapi.json — not committed; fetch
it when needed, see AGENTS.md). Each IRI endpoint maps to an MCP tool executed on
the `im` login node over SSH via remotemanager — there is no REST service; we
emulate the API's shape and semantics.

**The ✅/🔜/❌ verdicts below are specific to `im`.** They were re-decided against
what this machine can actually do, not inherited. `im` is a small CPU-first Slurm
cluster with **no GPUs, no enforced accounting, and no container runtime**, so the
allocation and container endpoints are N/A here (unlike machines that bill compute
or run containers). When porting onward, re-decide every row from scratch.

Legend: ✅ implemented · 🔜 planned next · ❌ deferred / N/A (with reason)

## facility

| IRI endpoint | Tool | Status | Notes |
|---|---|---|---|
| GET /facility | `get_facility` | ✅ | Static data from `data/imlab_config.json` |
| GET /facility/sites | — | ❌ | Single-site deployment |
| GET /facility/sites/{site_id} | — | ❌ | Same |

## status

| IRI endpoint | Tool | Status | Notes |
|---|---|---|---|
| GET /status/resources | `get_resources` | ✅ | One resource (`imlab`) with per-partition node summary from sinfo |
| GET /status/resources/{resource_id} | `get_resource` | ✅ | Per-partition node counts + drained nodes with reasons (`sinfo -R`) |
| GET /status/incidents | — | ❌ | No incident feed on this lab machine |
| GET /status/incidents/{id} | — | ❌ | Same |
| GET /status/events | — | ❌ | Same |
| GET /status/events/{id} | — | ❌ | Same |

## account

| IRI endpoint | Tool | Status | Notes |
|---|---|---|---|
| GET /account/capabilities | — | ❌ | No equivalent concept |
| GET /account/projects | `get_projects` | ✅ | `sacctmgr show assoc user=$USER` — **informational only** (accounting not enforced; account optional in a JobSpec) |
| GET /account/projects/{id} | `get_project` | ✅ | Filter over `get_projects` |
| GET .../project_allocations | — | ❌ N/A | **Re-decided for `im`:** `AccountingStorageEnforce=none` and no core-time budget — there is nothing to allocate. (Contrast: implemented on TSUBAME4, which bills TSUBAME points.) |
| GET .../project_allocations/{id} | — | ❌ N/A | Same |
| GET .../user_allocations | — | ❌ N/A | Same |
| GET .../user_allocations/{id} | — | ❌ N/A | Same |

## compute

| IRI endpoint | Tool | Status | Notes |
|---|---|---|---|
| POST /compute/job/{resource_id} | `submit_job` | ✅ | JobSpec → sbatch script (kept in `~/.imlab/jobs/`); returns `{job_id, script_path}` — see deviation |
| PUT /compute/job/{rid}/{job_id} | `update_job` | ✅ | `scontrol update job`; time_limit/name/partition/reservation |
| GET /compute/status/{rid}/{job_id} | `get_job_status` | ✅ | sacct (+ squeue reason for queued jobs) |
| POST /compute/status/{rid} | `get_job_statuses` | ✅ | Batch; empty list = current user's last 2 days |
| DELETE /compute/cancel/{rid}/{job_id} | `cancel_job` | ✅ | scancel + post-cancel state report |

## filesystem

| IRI endpoint | Tool | Status | Notes |
|---|---|---|---|
| GET /filesystem/ls | `fs_ls` | ✅ | |
| GET /filesystem/stat | `fs_stat` | ✅ | |
| GET /filesystem/view | `fs_view` | ✅ | 200KB cap; text only |
| GET /filesystem/head | `fs_head` | ✅ | |
| GET /filesystem/tail | `fs_tail` | ✅ | Primary way to read job output (`slurm-<id>.out`) |
| POST /filesystem/mkdir | `fs_mkdir` | ✅ | |
| POST /filesystem/upload | `fs_upload` | ✅ | Text or base64 binary via MCP; 5 MB cap |
| GET /filesystem/download | `fs_download` | ✅ | Base64; 5 MB cap; suggests scp for larger files |
| GET /filesystem/checksum | `fs_checksum` | ✅ | `sha256sum` |
| POST /filesystem/mv | `fs_mv` | ✅ | destructive (documented) |
| POST /filesystem/cp | `fs_cp` | ✅ | `cp -r` |
| DELETE /filesystem/rm | — | ❌ | Deliberately omitted (destructive); use the escape hatch with confirmation |
| PUT /filesystem/chmod | `fs_chmod` | ✅ | |
| PUT /filesystem/chown | `fs_chown` | ✅ | group-only changes work for normal users |
| POST /filesystem/symlink | `fs_symlink` | ✅ | `ln -s` |
| POST /filesystem/compress | `fs_compress` | ✅ | `tar` gzip/bzip2/xz/none + match_pattern |
| POST /filesystem/extract | `fs_extract` | ✅ | `tar -x` |

## task

| IRI endpoint | Tool | Status | Notes |
|---|---|---|---|
| GET /task/{task_id} | — | ❌ | SSH execution is synchronous — `submit_job` returns `job_id` directly |
| DELETE /task/{task_id} | — | ❌ | Same |
| GET /task | — | ❌ | Same |

## extensions (no IRI counterpart)

| Tool | Notes |
|---|---|
| `run_command_on_cluster` | Arbitrary login-shell command (e.g. `module avail`, `sinfo`, `squeue`, `sacct`). Marked as a non-IRI escape hatch. |

---

## Known deviations from the IRI/PSI-J schemas

### ResourceSpec — CPU-only

`im` has no GPUs, so the PSI/J `gpu_cores_per_process` field and any GPU extension
are **omitted**. ResourceSpec carries `node_count`, `process_count`,
`processes_per_node`, `cpu_cores_per_process`, `exclusive_node_use`, and `memory`
(bytes → `--mem`).

### JobAttributes

`account` is **optional** (accounting is not enforced on `im`; no default is
injected). `queue_name` defaults to `main`. `duration` defaults to 1h even though
partitions are unlimited, so jobs are scheduled predictably.

### No container support

There is no Apptainer/Singularity/Docker on `im`, so the IRI `Container` concept
is not implemented (dropped from JobSpec).

### JobState

Native states map from Slurm via `map_slurm_state`. Normalized values are
uppercase (`QUEUED`/`ACTIVE`/`COMPLETED`/`FAILED`/`CANCELED`/`HELD`/`UNKNOWN`).

### submit_job return value

Returns `{job_id, script_path}` rather than IRI's async `TaskSubmitResponse`,
because SSH execution is synchronous — sbatch completes before we return.

### resource_id

Accepted and validated in all compute/status tools, but there is a single
resource: `imlab`.
