---
name: imlab-submitting-jobs
description: Use when the user wants to run, submit, or launch a job (simulation, MPI/OpenMP program, CP2K/Quantum ESPRESSO/LAMMPS/DFTB+ run, benchmark) on the IMLab `im` cluster. Covers partition selection, JobSpec construction, modules, and submission.
---

# Submitting jobs on the `im` cluster

im is a small **CPU-first** cluster (3 AMD EPYC nodes, no GPUs) running Slurm.
Most work is MPI, or MPI+OpenMP hybrid, for computational chemistry.

## Workflow

1. **Pick the partition** — `get_facility` has the list. Rules of thumb:
   - General CPU / MPI work → `main` (default).
   - Long-running jobs → `long`.
   - Large-memory or whole-node jobs → `huge`.
   - Quick tests / debugging → `debug`.
   Wall-time is unlimited on all partitions, but still set a realistic `duration`.
2. **No account needed** — accounting is not enforced on im, so jobs submit
   without one and nothing is billed. (`attributes.account` is optional.)
3. **Stage any needed files** with `fs_upload` / `fs_mkdir` (paths are relative to
   the home directory unless absolute). Large data goes under `/data`.
4. **Submit with a JobSpec** via `submit_job`. Show the user the spec (or describe
   it) before submitting unless they asked to just run it. Describe CPU work with
   `processes_per_node` (MPI ranks) and `cpu_cores_per_process` (OpenMP threads);
   load software in `pre_launch`. Examples:

   Pure-MPI on one node (16 ranks), Quantum ESPRESSO:
   ```json
   {
     "name": "qe-run",
     "executable": "pw.x -in scf.in",
     "launcher": "srun",
     "pre_launch": "module purge && module load openmpi/5.0.7 quantum-espresso/7.3",
     "directory": "/home/<user>/run",
     "resources": {"node_count": 1, "processes_per_node": 16},
     "attributes": {"duration": "2:00:00", "queue_name": "main"}
   }
   ```

   Hybrid MPI+OpenMP across 2 nodes (4 ranks/node × 8 threads), CP2K:
   ```json
   {
     "name": "cp2k-run",
     "executable": "cp2k.psmp -i input.inp",
     "launcher": "srun --cpus-per-task=$SLURM_CPUS_PER_TASK",
     "pre_launch": "module purge && module load openmpi/5.0.7 cp2k/2025.2",
     "resources": {"node_count": 2, "processes_per_node": 4, "cpu_cores_per_process": 8},
     "environment": {"OMP_NUM_THREADS": "8"},
     "attributes": {"duration": "6:00:00", "queue_name": "long"}
   }
   ```
   The rendered sbatch script is kept on the cluster under `~/.imlab/jobs/` —
   `fs_view` it if the user wants to inspect what was submitted.
5. **Verify**: `get_job_status` right after submission. `QUEUED` with a message
   explains any wait; stdout lands in `<workdir>/slurm-<job_id>.out`.

## im conventions

- **CPU only (no GPUs)** — never request a GPU. Nodes are AMD EPYC 7713 (128
  cores on im1/im3, 64 on im2).
- **Modules**: load an MPI stack (`openmpi/5.0.7` newest, also 4.1.7 / 3.1.5) and
  an application (`cp2k/2025.2`, `quantum-espresso/7.3`, `lammps/22Jul2025`,
  `dftbplus/24.1`). Libraries: fftw, hdf5, netcdf, openblas, scalapack. Build and
  run with the **same** modules. `module avail` (via `run_command_on_cluster`)
  lists what's installed live.
- **Threads**: set `OMP_NUM_THREADS` to match `cpu_cores_per_process` for
  OpenMP/hybrid code, or it may run with an unintended thread count.
- **Memory**: default is unlimited; set `resources.memory` (bytes → `--mem`) only
  when a job needs a specific amount, or use `huge` for large-memory runs.
- **Time**: partitions are unlimited; still give a realistic `duration` (default
  1h) so the scheduler can plan.
- **No containers** — there is no Apptainer/Singularity/Docker on im; bring
  software via modules or build it in your home directory.
- **Storage**: `/home` (500 GB) for code, `/data` (9.1 TB) for large datasets.
  No dedicated scratch tier.

## Don't

- Don't run computation on the login node (im1) — submit a job.
- Don't request GPUs or containers — this cluster has neither.
- Don't guess im-specific details — use `search_docs` from the imlab-docs server.
- Don't `cancel_job` without confirming with the user.
