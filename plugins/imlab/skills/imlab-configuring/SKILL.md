---
name: imlab-configuring
description: Use when the user wants to set up, configure, or troubleshoot IMLab-Agent — SSH access to the `im` cluster login node (including the off-campus ProxyJump through the TSUBAME login node), or the ~/.imlab/config.json file. Also use when imlab tools fail with connection errors.
---

# Configuring IMLab-Agent

Settings live in `~/.imlab/config.json` (env vars `IMLAB_HOST`, `IMLAB_CONFIG`
override it):

```json
{
  "ssh": {"host": "imlab"}
}
```

The `im` cluster does **not** enforce accounting, so no account/project is needed
— `ssh.host` is the only required setting.

## Guided setup — interview the user, then write the file

Read the existing `~/.imlab/config.json` first (if any) and only ask about what's
missing or being changed.

1. **SSH** — the login node is `131.112.104.58` (host `im1`). Set up a **clean
   `~/.ssh/config` alias** so the agent has one unambiguous target (the user's
   config may already have several duplicate `Host 131.112.104.58` blocks — a
   named alias avoids that ambiguity). Offer to add:

   On the Institute network (direct):
   ```
   Host imlab
     HostName 131.112.104.58
     User <username>
     IdentityFile ~/.ssh/<key>
   ```

   Off-campus (hop through the TSUBAME login node):
   ```
   Host imlab
     HostName 131.112.104.58
     User <username>
     IdentityFile ~/.ssh/<key>
     ProxyJump login.t4.gsic.titech.ac.jp
   ```
   ProxyJump is handled entirely by SSH, so no plugin change is needed — the
   agent just uses the `imlab` alias.

   Then set `"host": "imlab"` in the config, and verify with:
   `ssh -o BatchMode=yes imlab 'echo ok'` (BatchMode matters — the MCP server
   cannot answer password prompts; key-based auth is required).

2. **Account** — not needed. im runs with accounting disabled, so jobs submit
   without one. (If the user ever wants to tag jobs to a Slurm account, they can
   set `"account"` in the config, but it's optional.)

3. **Write the file**, then `chmod 600 ~/.imlab/config.json`.

4. **Validate** with the doctor (checks config, SSH, Slurm, docs index):
   ```bash
   uv tool run --quiet --from ./server imlab-doctor
   ```
   (After publishing, the `git+https://…@main#subdirectory=server` form works too.)

## Notes

- Settings are read per-call; an SSH host change needs the imlab-hpc server
  restarted (reconnect MCP servers or restart the client).
- Docs search is BM25 keyword matching (no embedding endpoint) — works offline,
  no configuration needed.
