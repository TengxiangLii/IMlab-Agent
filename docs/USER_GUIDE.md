# IMLab-Agent — User Guide

This is the complete guide to using **IMLab-Agent**, a plugin that lets you
operate the IMLab **`im`** cluster (Institute of Science Tokyo) by talking to an
AI agent in ordinary language.

It's written for people who may be new to **both** compute clusters **and** AI
agents. You do not need to know Linux commands or job schedulers to use this.

**Contents**

1. [Understanding the agent workflow](#1-understanding-the-agent-workflow)
2. [The im cluster in five minutes](#2-the-im-cluster-in-five-minutes)
3. [What you can do with the agent](#3-what-you-can-do-with-the-agent)
4. [Worked examples](#4-worked-examples)
5. [Everyday recipes (cheat-sheet)](#5-everyday-recipes-cheat-sheet)
6. [Troubleshooting & FAQ](#6-troubleshooting--faq)
7. [Reference appendix](#7-reference-appendix)

If you haven't installed and connected the plugin yet, do the
[Quickstart](../QUICKSTART.md) first (about 5 minutes).

---

## 1. Understanding the agent workflow

### What "the agent" is

You already use an AI assistant (Claude Code or Codex). **IMLab-Agent adds a set
of abilities to it** so it can reach out and operate the `im` cluster on your
behalf. You type requests in plain English; the agent figures out the right
actions and carries them out.

Think of it as a knowledgeable lab-mate who *does* know all the cluster commands,
sitting between you and the machine:

- **You say** what you want ("run this on 16 cores for two hours").
- **The agent** translates that into the correct cluster operations, runs them
  over your SSH connection, and reports back in plain language.

### The old way vs. the agent way

Traditionally, using a cluster looks like this:

```
ssh you@131.112.104.58                     # log in
nano job.sh                                # write a script full of #SBATCH lines
sbatch job.sh                              # submit it to the scheduler
squeue -u you                              # check if it's running (cryptic table)
cat slurm-108441.out                       # find and read the output file
```

With the agent, the same thing is:

> **Run `pw.x -in scf.in` on 16 cores for two hours and tell me when it finishes.**

The agent writes the job script, submits it, watches it, and shows you the
output. You never memorize a flag.

### What the agent does for you vs. asks you

- It acts **using your SSH key** — the same access you'd have yourself. It cannot
  do anything on the cluster you couldn't do.
- It will usually **show you its plan** (what job it's about to submit) before
  acting.
- It **asks for confirmation before anything that deletes or overwrites data** —
  cancelling a job, removing or moving files.
- **Looking is free and safe.** Checking the queue, node status, or your files
  changes nothing.

### Skills and slash commands

The plugin ships with a few **skills** — pre-written playbooks the agent follows
for common workflows. You can trigger them explicitly by typing a slash command:

| Command | What it's for |
|---|---|
| `/imlab-demo` | A guided end-to-end tour that runs a small test job. |
| *(the others fire automatically)* | setup, submitting, monitoring, and looking up docs |

**You rarely need to type these.** Plain English triggers the right skill on its
own — *"help me submit a job"* activates the submitting-jobs skill; *"why did my
job fail?"* activates the monitoring skill. The slash commands are just a shortcut
when you want to be explicit.

### A note on trust and safety

- Read-only questions (status, node state, file listings, doc searches) are safe
  — ask freely.
- **Jobs on `im` aren't billed**, so running work costs nothing; but the agent
  still shows you a job before submitting it.
- You can always say *"cancel that job"* — the agent stops it.
- The agent works only within your account and your SSH access.

---

## 2. The im cluster in five minutes

Just enough background so the examples make sense.

### Login node vs. compute node

When you connect to `im` you land on the **login node** (`im1`) — a shared front
desk for editing files and submitting work. **You never run heavy computation
there** (it's shared and would slow things for everyone). Instead you submit a
**job**, which runs on a **compute node**. The agent always does this correctly
for you.

### What a "job" is

A **job** is a piece of work you hand to the **scheduler** (`im` uses **Slurm**).
The scheduler puts your job in a **queue**, waits until the resources you asked
for are free, runs it, and saves the output to a file. You get a **job ID** (a
number like `108441`) to track it.

### How you size a job

`im` is a small **CPU-first** cluster — three nodes built on AMD EPYC processors,
**no GPUs**. You size a job in plain CPU terms, and the agent turns it into a
Slurm request:

- **nodes** — how many machines (1, 2, or 3).
- **MPI ranks per node** — how many parallel processes per machine.
- **threads per rank** — for OpenMP/hybrid codes (the agent sets
  `OMP_NUM_THREADS` for you).
- **memory** — only if a job needs a specific amount.
- **partition** — which queue to use (below).

You don't have to memorize any of this — say *"run this on one node with 32 MPI
processes"* and the agent builds the right script.

**Partitions** are named queues for different kinds of run:

| partition | use for |
|---|---|
| `main` (default) | everyday CPU / MPI work |
| `long` | long-running jobs |
| `huge` | large-memory or whole-node jobs |
| `debug` | quick tests and short debugging runs |

Wall-time is effectively **unlimited** on every partition, but it's good practice
to give a realistic time estimate; the agent defaults to one hour if you don't.

### No billing

Unlike big supercomputers, `im` does **not** charge for compute — there are no
"points," budgets, or required project accounts. You just run. (This is why the
setup doesn't ask for an account.)

### Where to keep your files

| Location | Size | Use it for |
|---|---|---|
| `/home/<you>` | 500 GB (shared) | code, scripts, small files |
| `/data` | 9.1 TB (shared) | large datasets and results |

The agent can move files between your laptop and these locations, and report your
usage.

### Software: modules

Software on `im` is loaded with **modules**. A typical job loads an MPI stack and
an application, e.g. `module load openmpi/5.0.7` then `quantum-espresso/7.3`. The
agent adds the right `module load` lines to your job for you. Installed codes
include **CP2K, Quantum ESPRESSO, LAMMPS, DFTB+,** and **BigDFT**, plus numerical
libraries (FFTW, HDF5, NetCDF, OpenBLAS, ScaLAPACK).

There is **no container runtime** on `im` (no Apptainer/Docker) — software comes
through modules or you build it in your home directory.

---

## 3. What you can do with the agent

Everything below is just a matter of *asking*. Grouped by kind of task:

**Explore the machine**
- *"Describe the im cluster."* — nodes, partitions, storage.
- *"Is the cluster busy right now? Where would my job start fastest?"*

**Work with files**
- *"List my home directory."* / *"Show me the last 30 lines of results.log."*
- *"Upload this input file to the cluster."* / *"Download that output file to my
  laptop."*
- *"Make a folder called runs."* / *"Compress that results directory."*

**Submit jobs**
- *"Run `pw.x -in scf.in` on 16 cores for two hours."*
- *"Submit a 2-node MPI job, 32 processes per node, on the long partition."*
- *"Run my CP2K input as a hybrid MPI+OpenMP job."*

**Monitor and debug**
- *"What are my jobs doing right now?"*
- *"Is job 108441 done yet?"*
- *"My job failed — why? Show me the error."*
- *"Cancel job 108441."* / *"Give job 108441 another hour of runtime."*

**Look things up**
- *"How do I run Quantum ESPRESSO here?"* / *"Which OpenMPI versions are
  available?"* — the agent searches the built-in guide and can list installed
  software live.

**Anything else**
- For a task no built-in ability covers, the agent can run a specific command on
  the cluster for you (for example, `module avail` to list software). Just
  describe what you need.

---

## 4. Worked examples

Each example shows **what you say**, **what the agent does**, and **what you get
back**. Prompts are in quotes — type them in your own words; you don't have to
match them exactly.

### Example 1 — Is the cluster busy?

> **Is the im cluster busy right now? Where would a job start soonest?**

The agent checks the live node state per partition and reports how many nodes are
free, then tells you which partition has capacity. Costs nothing.

### Example 2 — Run a simulation on one node

> **Upload `scf.in` from my current folder, then run Quantum ESPRESSO's `pw.x` on
> it using 16 MPI processes on one node, for two hours.**

The agent will:
1. Upload `scf.in` to the cluster.
2. Build a job with 1 node / 16 ranks, `module load openmpi/5.0.7 quantum-espresso/7.3`,
   launched with `srun`.
3. **Show you the plan** and submit it, returning the job ID.

Then follow up: *"Tell me when it's done and show the output."*

### Example 3 — A hybrid MPI+OpenMP job across two nodes

> **Run my CP2K input `run.inp` across 2 nodes, 4 processes per node with 8
> threads each, on the long partition.**

The agent picks the layout (2 nodes × 4 ranks × 8 threads), sets
`OMP_NUM_THREADS=8`, writes the script with `module load openmpi/5.0.7 cp2k`, and
submits it. You didn't write a single scheduler directive.

### Example 4 — Diagnose a failed job

> **My job 108441 failed. What went wrong?**

The agent reads the job's record and its `slurm-108441.out` file, then explains in
plain language — for example *"it ran out of memory; try more memory or the huge
partition"* or *"the wrong OpenMPI module was loaded."* Common causes it can spot:
out of memory, wrong thread/rank layout, or a module mismatch.

### Example 5 — Manage a running job

> **What are my jobs doing?** → agent lists them with states.
>
> **Cancel job 108441.** → agent confirms, then stops it.
>
> **Actually, give job 108441 another hour instead.** → agent extends its time
> limit.

### Example 6 — Look up how to use an application

> **How do I run LAMMPS on im, and which version is installed?**

The agent searches the built-in guide and can list the live `module avail` output,
then help you build a job for it.

### Example 7 — A quick free test

> **Submit a tiny test job that prints the compute node's hostname on 4 processes.**

The agent submits a small MPI `hostname` job on the `debug` partition, waits a few
seconds, and shows you the output — a node name (`im1`/`im2`/`im3`) once per
process. Great for confirming things work. (This is what `/imlab-demo` does.)

---

## 5. Everyday recipes (cheat-sheet)

| Your goal | Say something like… |
|---|---|
| See the machine's specs | "Describe the im cluster." |
| Check how busy it is | "How busy is the cluster right now?" |
| Check disk usage | "How much space am I using in /home and /data?" |
| List files | "Show me my home directory." |
| Read a file / job output | "Show the last 40 lines of results.log." |
| Send a file to the cluster | "Upload run.inp to my home directory." |
| Get a file back | "Download output.tar.gz to my laptop." |
| Run on N cores | "Run this on 32 MPI processes on one node for 2 hours." |
| Hybrid MPI+OpenMP | "Run this on 2 nodes, 4 ranks/node, 8 threads each." |
| Big-memory job | "Run this on the huge partition." |
| Quick test | "Submit a small test job of `hostname` on debug." |
| Check a job | "Is job 108441 done?" |
| List my jobs | "What are my jobs doing?" |
| Debug a failure | "Why did job 108441 fail?" |
| Cancel | "Cancel job 108441." |
| More time | "Give job 108441 another hour." |
| Look something up | "Which OpenMPI versions are installed?" |

---

## 6. Troubleshooting & FAQ

**"The agent says it's not configured."**
Run setup: *"set up my im connection."* It creates `~/.imlab/config.json` with
your SSH host. You can check that file exists and is correct.

**"Permission denied" or it's asking for a password.**
`im` accepts **SSH keys only**. You should be able to `ssh <you>@131.112.104.58`
from your own terminal. From off-campus you reach `im` by hopping through the
TSUBAME login node — the agent's setup can add a `ProxyJump` line to your
`~/.ssh/config` so this is automatic. The agent cannot answer password prompts.

**My job was rejected or never starts.**
On `im` this is about resources, not budget (there's no billing). Ask *"is the
cluster busy?"* — your job may be waiting for nodes to free up. If it's rejected,
ask the agent to show the error; it's usually an impossible request (more nodes
than exist, or a bad partition name).

**My job failed / ran badly.** Tell the agent *"why did job N fail?"* and it will
read the logs. Common fixes it will suggest:
- *Out of memory* → ask for more memory, fewer processes per node, or the `huge`
  partition.
- *Slow / wrong thread count* → the agent sets `OMP_NUM_THREADS`; mention it's a
  threaded (OpenMP/hybrid) program.
- *Module mismatch* → build and run with the same modules; the agent loads a
  single MPI stack.

**I saw something about "rsync version 2.6.9."**
Nothing to do — the plugin handles this automatically. (On macOS the system rsync
is old, but the agent only uses direct SSH, so it doesn't matter.)

**Does the agent cost anything to use?**
No. `im` doesn't bill compute, and looking around (status, files, docs) changes
nothing. Submitting jobs is free too — the agent just shows you a job first.

**I use Codex, not Claude Code.**
Everything works the same — you talk to the agent in plain English. The only
differences are install (`codex plugin marketplace add TengxiangLii/IMlab-Agent`,
then install via `/plugins`) and that you invoke skills from the `/plugins` menu.
All the example prompts above apply unchanged.

---

## 7. Reference appendix

### Nodes

| Node | CPU | Cores | Memory | Role |
|---|---|---|---|---|
| `im1` | AMD EPYC 7713 ×2 | 128 | ~514 GB | login + compute |
| `im2` | AMD EPYC | 64 | ~257 GB | compute |
| `im3` | AMD EPYC 7713 ×2 | 128 | ~257 GB | compute |

No GPUs. Scheduler: Slurm 24.05.

### Partitions

| Partition | Wall time | Use for |
|---|---|---|
| `main` *(default)* | unlimited | everyday CPU / MPI work |
| `long` | unlimited | long-running jobs |
| `huge` | unlimited | large-memory / whole-node jobs |
| `debug` | unlimited | quick tests and short debugging |

### Storage

| Path | Size | Purpose |
|---|---|---|
| `/home/<you>` | 500 GB (shared, xfs) | code, scripts, small files |
| `/data` | 9.1 TB (shared, xfs) | large datasets and results |

No Lustre and no dedicated per-job scratch tier.

### Software (modules)

- **MPI:** `openmpi/5.0.7` (newest), `4.1.7`, `3.1.5`
- **Applications:** `cp2k/2025.2`, `quantum-espresso/7.3`, `lammps/22Jul2025`,
  `dftbplus/24.1` (+ serial), `bigdft`
- **Libraries:** `fftw` (+mpi), `hdf5`, `netcdf`, `openblas`, `scalapack`

Versions change — ask the agent to run `module avail` for the current list.

### The skills (and when they fire)

| Skill / command | Fires when you… |
|---|---|
| `imlab-configuring` | ask to set up or fix your connection |
| `imlab-submitting-jobs` | ask to run/submit/launch a job |
| `imlab-monitoring-jobs` | ask about job status, output, or failures |
| `imlab-reference` | ask a factual question about the cluster |
| `/imlab-demo` | want the guided end-to-end tour (run it explicitly) |

### Settings file

`~/.imlab/config.json`:

```json
{
  "ssh": {"host": "imlab"}
}
```

`ssh.host` is a `~/.ssh/config` alias (or `user@131.112.104.58`). The environment
variable `IMLAB_HOST` overrides the file. No account is needed — `im` doesn't
bill compute.

### Getting help

For accounts, access, or policy questions the agent can't answer, contact the
IMLab administrators. The agent can always search the built-in guide or check the
cluster's live state — just ask.
