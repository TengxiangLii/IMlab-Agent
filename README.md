# IMLab-Agent

Claude Code and Codex plugin for the IMLab **`im`** cluster (Institute of Science Tokyo) — submit and monitor Slurm jobs, manage files on the cluster, and search the built-in documentation, all from the agent.

`im` is a small CPU-first cluster: three AMD EPYC nodes running Slurm for MPI/OpenMP computational-chemistry work (CP2K, Quantum ESPRESSO, LAMMPS, DFTB+) — no GPUs, and no accounting, so jobs just run.

## Install

### Prerequisite: uv

The plugin starts its MCP servers with `uv tool run` from this repository's
`main` branch, so `uv` must be installed and available on your PATH before
Claude Code or Codex starts the plugin.

Common install options:

```bash
brew install uv
```

or:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

After installing uv, restart Claude Code or Codex so the plugin process inherits
the updated PATH.

### Claude Code

Install in Claude Code:

```
/plugin marketplace add TengxiangLii/IMLab-Agent
/plugin install imlab@imlab-marketplace
/reload-plugins
```

### Codex

Install in Codex:

```
codex plugin marketplace add TengxiangLii/IMLab-Agent
```

Then open `/plugins`, install `imlab`, start a new thread, and run
`/imlab-demo` to verify the connection end-to-end.

## Configuration

Settings live in `~/.imlab/config.json`:

```json
{
  "ssh": {"host": "imlab"}
}
```

- `ssh.host` is a `~/.ssh/config` alias or `user@hostname` (key-based auth required). The login node is `131.112.104.58` (im1) — reachable directly on the Institute network, or via a `ProxyJump` through the TSUBAME login node off-campus (set that in `~/.ssh/config`; the agent just uses the alias). The env var `IMLAB_HOST` overrides the file.
- No account is needed — the `im` cluster does not enforce Slurm accounting, so jobs submit without one. (An optional `account` field can tag jobs if you ever want to.)

Documentation search ships as a BM25 keyword index and works fully offline — no configuration needed. Only if you have your own embedding endpoint should you add `embedding.base_url`, `embedding.model`, and `embedding.api_key` (via `IMLAB_EMBED_API_KEY`) and rebuild the index; otherwise search stays on BM25 keyword matching over the same content.
