---
name: imlab-demo
description: Interactive demo of IMLab-Agent — walks through facility info, live cluster status, docs search, filesystem access, and a small CPU/MPI job on the `im` cluster.
user-invocable: true
---

# IMLab-Agent demo

Run each step in order. Present results as a readable narrative — not raw JSON
dumps. Use markdown headers and tables to make it scannable. Pause after each step
and show output before moving on.

---

## Step 1 — Facility overview

Call `get_facility`. Present the key facts as a short table:
- Nodes: im1 / im2 / im3 — cores and memory each
- Partitions: main / long / huge / debug
- Storage: /home, /data

Lead with one sentence: **"im is IMLab's small CPU-first Slurm cluster — three
AMD EPYC nodes for MPI/OpenMP computational chemistry, no GPUs."**

---

## Step 2 — Live cluster status

Call `get_resources`. For each partition, show a mini utilization view
(allocated vs idle nodes) and point out where a job would start fastest.

---

## Step 3 — Documentation search

Call `search_docs` with *"how do I run an MPI job and which partitions exist?"*

Show the top result: the breadcrumb, a short excerpt, and the source. It will note
`[search_method: bm25]` — say: *"Running on BM25 keyword search, which ships with
the plugin and works fully offline."*

---

## Step 4 — Filesystem

Call `fs_ls(".")` to list the user's home directory. Show it cleanly. Then
demonstrate the toolkit:
1. `fs_upload("/tmp/imlab-demo.txt", "hello from IMLab-Agent\n")` — write a file
2. `fs_checksum("/tmp/imlab-demo.txt")` — show the SHA-256
3. `fs_cp(...)` then `fs_checksum` on the copy — confirm the checksum matches

Present this as: *"Upload, checksum, copy — the filesystem toolkit."*

---

## Step 5 — Recent jobs

Call `get_job_statuses([])` (empty list = last 2 days). If there are jobs, show
them as a table: job ID | name | state | partition | elapsed. If none, say so and
move to Step 6.

---

## Step 6 — Test job

Tell the user: *"Let's submit a quick CPU test job to verify end-to-end submission
and output."* Jobs on im aren't billed, so no account is needed.

Submit via `submit_job` with this spec (a tiny MPI `hostname` on the `debug`
partition):
```json
{
  "name": "imlab-demo",
  "executable": "hostname",
  "launcher": "srun",
  "resources": {"node_count": 1, "processes_per_node": 4},
  "attributes": {"duration": "0:05:00", "queue_name": "debug"}
}
```

Show the rendered job ID and script path. Then call `get_job_status(<job_id>)`
immediately and report the initial state.

---

## Step 7 — Monitor and read output

Poll `get_job_status` every ~10 seconds (use `run_command_on_cluster("sleep 10")`
to wait). Stop when the state is `completed` or `failed` (or after ~5 polls — tell
the user to check back with `get_job_status` if it's still queued).

Once completed, read `<workdir>/slurm-<job_id>.out` with `fs_tail` and show the
output — it should list the compute node's hostname (im1/im2/im3), repeated once
per MPI rank.

---

## Closing

Summarize in 5 bullets:
- Facility and live cluster status checked
- Documentation searched (MPI + partitions)
- Filesystem explored with upload, checksum, and copy
- A small MPI job submitted, ran, and its output retrieved
- Everything went through one SSH layer to the im login node

Then say: *"From here you can submit real workloads with /imlab-submitting-jobs,
monitor them with /imlab-monitoring-jobs, or ask anything about the cluster."*
