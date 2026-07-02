---
name: imlab-reference
description: Use when answering any question about `im` cluster specifics — login, partitions, modules, storage, policies — or when unsure about a cluster detail. Search the built-in guide or check live state instead of guessing.
---

# im cluster documentation reference

Do not answer im-specific questions from memory — ground answers in the built-in
guide, and prefer live state for anything that changes over time.

## Workflow

1. `search_docs` (imlab-docs server) with the user's question. Cite the returned
   source in your answer.
2. If results look incomplete, `list_doc_sections` shows the full table of
   contents; `read_doc_section` reads a section in full by its breadcrumb.
3. For anything current or precise — installed software, queue occupancy, node
   state — **check live state**:
   - `get_facility` / `get_resources` (imlab-hpc) for nodes/partitions and state.
   - `run_command_on_cluster` for `module avail` (software), `sinfo` (nodes),
     `squeue` (queue), `sacct` (history).
4. For accounts or policy, point the user to the IMLab administrators.

## Orientation (stable facts)

- **CPU-first machine, no GPUs.** 3 nodes: `im1` (login + compute, 128 cores,
  514 GB), `im3` (128 cores, 257 GB), `im2` (64 cores, 257 GB). AMD EPYC 7713.
- **Scheduler**: Slurm 24.05. Partitions `main` (default), `long`, `huge`,
  `debug` — all with unlimited wall time.
- **No billing**: accounting is not enforced; jobs run without an account.
- **Modules**: Environment Modules. MPI `openmpi/{3.1.5,4.1.7,5.0.7}`; apps
  `cp2k/2025.2`, `quantum-espresso/7.3`, `lammps/22Jul2025`, `dftbplus/24.1`,
  `bigdft`; libs fftw/hdf5/netcdf/openblas/scalapack.
- **No containers** (no Apptainer/Singularity/Docker).
- **Storage**: `/home` (500 GB) for code, `/data` (9.1 TB) for large data. xfs,
  not Lustre; no dedicated scratch tier.
- **Login**: `131.112.104.58` (im1); key-based SSH, direct on-campus or via a
  ProxyJump through the TSUBAME login node off-campus.

## Keeping the guide fresh

The docs index is built from `server/imlab_mcp/data/imlab_guide.md` (an original
guide). To revise it, edit that file and rebuild:
`python -m imlab_mcp.rag.ingest --no-embed` (BM25). Search uses BM25 keyword
matching by default.
