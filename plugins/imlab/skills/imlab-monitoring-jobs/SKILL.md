---
name: imlab-monitoring-jobs
description: Use when the user asks about the status, progress, output, history, or failure of jobs on the IMLab `im` cluster, or about node/queue availability.
---

# Monitoring jobs on the `im` cluster

## Status checks

- **One job**: `get_job_status` — `state` is normalized (QUEUED/ACTIVE/COMPLETED/
  FAILED/CANCELED); `native_state` is Slurm's (PD/R/CG/CD/CA/F/NF/TO…). A QUEUED
  job's `message` says why it waits (`Resources`, `Priority`, …).
- **My recent jobs**: `get_job_statuses` with an empty list (last 2 days), or pass
  specific IDs.
- **Cluster availability**: `get_resources` — per-partition allocated/idle/other/
  total node counts. Idle nodes can start jobs immediately.

## Job output and failure triage

1. Stdout/stderr default to `<workdir>/slurm-<job_id>.out` (workdir is in the
   status record). Read with `fs_tail` (or `fs_head`/`fs_view`).
2. Common im failure modes:
   - **OOM** → `native_state` OUT_OF_MEMORY; raise `resources.memory`, use fewer
     ranks per node, or move to the `huge` partition.
   - **Wrong thread/rank count** → performance collapse when `OMP_NUM_THREADS`
     wasn't set, or when ranks×threads oversubscribed a node's cores; check the
     script and the `cpu_cores_per_process`/`OMP_NUM_THREADS` pairing.
   - **Module / MPI mismatch** → build- and run-time modules differ, or the wrong
     `openmpi` version was loaded; `module purge` first, then load one MPI stack.
   - **Time limit** → only if a `--time` was set low; raise `duration` (partitions
     themselves are unlimited).
3. The exact script that was submitted is kept in `~/.imlab/jobs/` — `fs_view` it
   when debugging.

## Live job inspection

For an ACTIVE job, peek at its node with
`run_command_on_cluster("squeue --jobs=<id> --long")` for the node list, then
`run_command_on_cluster("srun --overlap --jobid <id> top -bn1")` for a quick look
at the allocated node.
