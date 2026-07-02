# The im cluster

An original, plain-language orientation to the **im** cluster (IMLab, Institute
of Science Tokyo), written for users who drive it through IMLab-Agent. It records
the site-specific facts that shape how you ask for work — not general HPC/Linux
background, and not a command reference. Stable facts (node shapes, partitions,
paths) are stated here so the agent can size a job without a round-trip; genuinely
changing values (queue occupancy, installed versions) are left to the live
system, which the agent queries on demand.

## What im is

im is a small **CPU-first** cluster scheduled with **Slurm**, used mainly for
computational-chemistry and materials simulations (CP2K, Quantum ESPRESSO, LAMMPS,
DFTB+, BigDFT). It has **three nodes** built on AMD EPYC (Zen3) CPUs — `im1`
(also the login node) and `im3` with 128 cores each, `im2` with 64 — and 257–514
GB of memory per node. There are **no GPUs**: think CPU, MPI, and OpenMP, and
describe jobs in nodes, ranks, and threads.

## Getting on the system

You reach im by SSH to `131.112.104.58` (host `im1`). On the Institute network you
can connect directly; from outside, hop through the TSUBAME login node as an SSH
`ProxyJump` — the agent uses whatever alias you set in `~/.ssh/config`, so the jump
is transparent once configured. Authentication is by SSH key.

The login node `im1` is shared and lightly resourced. Use it for editing,
building, staging files, and submitting — anything heavier belongs in a job, which
the agent submits for you.

## Running jobs: partitions, ranks, and threads

You describe a job in CPU terms and the agent turns it into a Slurm submission:
how many **nodes**, how many **MPI ranks per node**, how many **OpenMP threads per
rank**, how much **memory**, and which **partition**. You do not write batch
scripts or recall Slurm flags.

Pick a partition for the kind of run:

| partition | use for |
|---|---|
| `main` (default) | everyday CPU / MPI work |
| `long` | long-running jobs |
| `huge` | large-memory or whole-node jobs |
| `debug` | quick tests and short debugging runs |

Wall-time limits are effectively **unlimited** on every partition, but it's still
good practice to give a realistic time so the scheduler can plan; the agent
defaults to one hour if you don't say. Memory is not capped by default — ask for
a specific amount only when a job needs it.

**Jobs are not billed.** Slurm accounting is not enforced on im, so no project,
account, or budget is required to submit — you just run.

## Software: modules and MPI

Software comes from **Environment Modules**. A typical job loads an MPI stack and
an application, for example `module load openmpi/5.0.7` and then a code like
`cp2k/2025.2`, `quantum-espresso/7.3`, or `lammps/22Jul2025`. Numerical libraries
(FFTW, HDF5, NetCDF, OpenBLAS, ScaLAPACK) are available as modules too. Because
versions change, have the agent list what's installed live rather than relying on
a frozen list — but a few conventions are stable:

- **Load the same modules to build and to run.** Mismatched MPI versions between
  build and run time are a common source of failures.
- **Launch MPI with `srun` or `mpirun`.** Under Slurm, `srun` inherits the job's
  allocation. Match the MPI module you load (`openmpi/5.0.7` is the newest).
- **Tell threaded code its thread count** — set `OMP_NUM_THREADS` to the cores
  you reserve per rank, or it may run with the wrong number and far slower.

There is **no container runtime** on im (no Apptainer/Singularity/Docker), so
bring software through modules or build it in your home directory.

## Storage

Two places to keep data:

- `/home/<user>` — 500 GB shared area for code, scripts, and small files.
- `/data` — 9.1 TB shared area for large datasets and results.

There is no Lustre and no dedicated per-job scratch tier, so stage inputs and
write outputs under `/home` or `/data`. The agent can move files between your
laptop and these areas and report usage.

## Running work through the agent

You describe a job in resource terms — nodes, ranks per node, threads per rank,
memory, wall time, and partition — and the agent assembles and submits the Slurm
job, then returns a job ID to track. Most jobs are pure-MPI or a hybrid of MPI
across nodes with OpenMP threads within each node.

## Following jobs and untangling failures

After submission, a job's queue position, state, and history come from Slurm —
ask the agent and it reports back in plain language, including why a waiting job
is waiting. A job's console output is written to `slurm-<jobid>.out` in the
directory it was launched from, which the agent can read and summarize.

When a job misbehaves, the cause is usually one of a few:

- It ran out of memory — raise `--mem`, use fewer ranks per node, or move to
  `huge`.
- Its thread count was left unset, so performance collapsed — set
  `OMP_NUM_THREADS`.
- The wrong MPI module was loaded, or build- and run-time modules didn't match.
- A rank/thread layout that oversubscribed a node's cores.

The agent can inspect the failed job's record and output to point at which it was.

## Staying current

Installed software and node availability change over time. The authoritative
source is the live state of the machine, which the agent can query whenever a
precise, current answer matters (`module avail`, `sinfo`, `squeue`, `sacct`). For
anything about accounts or policy, ask the IMLab administrators.
