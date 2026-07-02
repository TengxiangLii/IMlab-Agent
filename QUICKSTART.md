# Quickstart — your first im-cluster job in ~5 minutes

**What this is:** IMLab-Agent lets you use the IMLab `im` cluster by **talking to
an AI agent in plain English**. Instead of learning Linux commands and the Slurm
job scheduler, you say things like *"run my simulation on 16 cores for two hours"*
and the agent does it for you over your SSH connection.

This page gets you from zero to a real job. For the full manual, see
[`docs/USER_GUIDE.md`](docs/USER_GUIDE.md).

---

## 1. Before you start

You need four things (one-time):

1. **An account on the `im` cluster.** If you don't have one, ask the IMLab
   administrators.
2. **Your SSH public key on the cluster**, and the ability to reach it. `im`
   allows key-based login only — no passwords. The login node is `131.112.104.58`
   (`im1`): reachable directly on the Institute network, or from outside by
   hopping through the TSUBAME login node (an SSH `ProxyJump`). If you can already
   run `ssh <you>@131.112.104.58` from your terminal, you're set.
3. **`uv`** — a small tool that launches the agent's cluster connector. Install
   with `brew install uv` (macOS) or `curl -LsSf https://astral.sh/uv/install.sh | sh`,
   then **restart** Claude Code / Codex so it sees `uv`.
4. **Claude Code** (this guide's focus) or **Codex**.

> **New to all of this?** Don't worry — you won't type any cluster commands
> yourself. The agent handles them. Read the
> [User Guide](docs/USER_GUIDE.md) for a gentle explanation of everything.

---

## 2. Install the plugin (Claude Code)

In Claude Code, run these three commands:

```
/plugin marketplace add TengxiangLii/IMlab-Agent
/plugin install imlab@imlab-marketplace
/reload-plugins
```

> **Codex:** run `codex plugin marketplace add TengxiangLii/IMlab-Agent`,
> then open `/plugins` and install `imlab`.

---

## 3. Connect it to your account

Just tell the agent, in plain English:

> **Set up my im-cluster connection.**

It will walk you through a short setup (which SSH host/alias to use — including
the off-campus ProxyJump if you need it) and write a small settings file at
`~/.imlab/config.json` that looks like this:

```json
{
  "ssh": {"host": "imlab"}
}
```

(`imlab` is an alias you add to `~/.ssh/config` pointing at `131.112.104.58`; the
agent can set that up for you. There's no account or password to configure — `im`
doesn't bill compute.)

Then check the connection:

> **Run the im doctor / check my connection.**

You want to see `✓ ssh` and `✓ slurm`.

---

## 4. Run your first job

The built-in demo runs a tiny real test job end to end. Just say:

> **/imlab-demo**

The agent will, step by step: describe the machine, show how busy it is, search
the docs, poke around your files, and then **submit a tiny MPI test job** on the
`debug` partition and read back its output. A successful run prints a compute
node's name (`im1`, `im2`, or `im3`) once per process — proof the whole chain
works end to end.

Jobs on `im` aren't billed, so this costs nothing.

---

## 5. What next

- Read the **[User Guide](docs/USER_GUIDE.md)** — what you can do, dozens of
  example prompts, and troubleshooting.
- Or just start asking. Try: *"Is the cluster busy right now?"* or *"Show me
  what's in my home directory."*
