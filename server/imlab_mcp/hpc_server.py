"""MCP server for the `im` cluster, modeled on the IRI Facility API.

Tool groups mirror the IRI resource groups (facility, status, account, compute,
filesystem); each operation is executed on the im login node over SSH via
remotemanager, since im does not expose a REST facility API itself. Coverage of
the full API is tracked in IRI_CHECKLIST.md at the repo root.
"""
import shlex

from mcp.server.fastmcp import FastMCP

from imlab_mcp import compute, config
from imlab_mcp.middleware import quote_path, run_command, write_remote_file
from imlab_mcp.models import CompressionType, Job, JobSpec
from imlab_mcp.serving import serve

mcp = FastMCP("imlab-hpc")

RESOURCE_ID = "imlab"


def _check_resource(resource_id: str) -> None:
    if resource_id != RESOURCE_ID:
        raise ValueError(f"Unknown resource '{resource_id}'; this server manages '{RESOURCE_ID}'")


# === facility ================================================================

@mcp.tool()
def get_facility() -> dict:
    """Describe the im facility: nodes, partitions, modules, storage, conventions.

    Static reference data (no SSH round-trip). im is a small CPU-first cluster
    (3 AMD EPYC nodes, no GPUs) running Slurm for MPI/OpenMP work. (IRI: GET /facility)
    """
    return config.load_cluster_config()


# === status ==================================================================

@mcp.tool()
def get_resources() -> list[dict]:
    """List compute resources and their live state. (IRI: GET /status/resources)

    Returns the im resource with a per-partition node-state summary
    (allocated/idle/other/total) from sinfo.
    """
    return [_resource_detail()]


@mcp.tool()
def get_resource(resource_id: str = RESOURCE_ID) -> dict:
    """Get detailed state for a single resource. (IRI: GET /status/resources/{resource_id})

    Includes per-partition node counts and any drained/draining nodes with
    their reasons (from sinfo -R).
    """
    _check_resource(resource_id)
    return _resource_detail(include_drain=True)


def _resource_detail(include_drain: bool = False) -> dict:
    summary = run_command("sinfo --summarize --format='%P|%a|%l|%F'")
    partitions = []
    for line in summary.strip().splitlines():
        parts = line.split("|")
        if len(parts) != 4 or parts[0] == "PARTITION":
            continue
        alloc, idle, other, total = parts[3].split("/")
        partitions.append({
            "partition": parts[0].rstrip("*"),
            "available": parts[1],
            "time_limit": parts[2],
            "nodes": {"allocated": int(alloc), "idle": int(idle),
                      "other": int(other), "total": int(total)},
        })
    resource: dict = {
        "id": RESOURCE_ID,
        "type": "compute",
        "description": "im cluster (AMD EPYC, x86_64; CPU-first MPI/OpenMP, no GPUs)",
        "partitions": partitions,
    }
    if include_drain:
        drain = run_command("sinfo -R --format='%N|%T|%E' --noheader")
        drained = []
        for line in drain.strip().splitlines():
            parts = line.split("|", 2)
            if len(parts) == 3:
                drained.append({"nodes": parts[0], "state": parts[1], "reason": parts[2]})
        resource["drained_nodes"] = drained
    return resource


# === account =================================================================
# im does not enforce Slurm accounting (AccountingStorageEnforce=none) and has no
# core-time budget, so the IRI allocation endpoints do not apply. get_projects is
# kept as informational (which Slurm account a user is associated with).

@mcp.tool()
def get_projects() -> list[dict]:
    """List the Slurm accounts the current user is associated with (informational).
    (IRI: GET /account/projects)

    On im, accounting is not enforced and jobs run without an --account, so this
    is informational only — an account is optional in a JobSpec. Each entry's id
    can be passed as JobAttributes.account if you want jobs tagged to it.
    """
    output = run_command(
        "sacctmgr -n show assoc user=$USER format=Account%30,Partition,QOS%20 2>/dev/null || true"
    )
    projects = []
    seen = set()
    for line in output.strip().splitlines():
        parts = [p.strip() for p in line.split("|")] if "|" in line else line.split()
        if not parts or not parts[0]:
            continue
        acct = parts[0]
        if acct in seen:
            continue
        seen.add(acct)
        projects.append({"id": acct})
    return projects


@mcp.tool()
def get_project(project_id: str) -> dict:
    """Get details for a single Slurm account. (IRI: GET /account/projects/{id})

    Informational only on im (no allocation/budget is tracked).
    """
    for p in get_projects():
        if p["id"] == project_id:
            return p
    raise ValueError(f"Account '{project_id}' not found for current user")


# === compute =================================================================

@mcp.tool()
def submit_job(spec: JobSpec, resource_id: str = RESOURCE_ID) -> dict:
    """Submit a job described by a JobSpec. (IRI: POST /compute/job/{resource_id})

    The spec is rendered as an sbatch script (kept under ~/.imlab/jobs/ on the
    cluster for auditability) and submitted. Returns the job_id and the script
    path. im notes: it is CPU-only (no GPUs) — describe work with
    resources.node_count, processes_per_node (MPI ranks) and cpu_cores_per_process
    (OpenMP threads), and resources.memory (bytes → --mem); pick a partition with
    attributes.queue_name (main/long/huge/debug; main is the default); load
    software in pre_launch (e.g. 'module load openmpi/5.0.7'); an account is
    optional (accounting is not enforced).
    """
    _check_resource(resource_id)
    return compute.submit(spec)


@mcp.tool()
def get_job_status(job_id: str, resource_id: str = RESOURCE_ID) -> Job:
    """Get the normalized status of one job. (IRI: GET /compute/status/...)

    state is the normalized IRI state (QUEUED/ACTIVE/COMPLETED/FAILED/CANCELED);
    native_state is Slurm's. For queued jobs, message explains the wait. Job
    stdout defaults to <workdir>/slurm-<job_id>.out — read it with fs_tail or
    fs_view.
    """
    _check_resource(resource_id)
    jobs = compute.get_statuses([job_id])
    if not jobs:
        raise ValueError(f"Job {job_id} not found")
    return jobs[0]


@mcp.tool()
def get_job_statuses(job_ids: list[str], resource_id: str = RESOURCE_ID) -> list[Job]:
    """Get statuses for several jobs at once, or recent jobs when job_ids is
    empty. (IRI: POST /compute/status/{resource_id})
    """
    _check_resource(resource_id)
    if job_ids:
        return compute.get_statuses(job_ids)
    # No IDs given: current user's jobs from the last two days.
    return compute.get_recent_statuses()


@mcp.tool()
def update_job(
    job_id: str,
    time_limit: str | None = None,
    name: str | None = None,
    partition: str | None = None,
    reservation: str | None = None,
    resource_id: str = RESOURCE_ID,
) -> Job:
    """Update a queued or running job. (IRI: PUT /compute/job/{resource_id}/{job_id})

    All fields are optional — only supplied ones are changed.
    time_limit: new wall time as HH:MM:SS or D-HH:MM:SS (works on running jobs too).
    partition, reservation: only valid while the job is still queued.
    """
    _check_resource(resource_id)
    mapping = {
        "TimeLimit": time_limit,
        "Name": name,
        "Partition": partition,
        "Reservation": reservation,
    }
    updates = " ".join(f"{k}={shlex.quote(v)}" for k, v in mapping.items() if v is not None)
    if not updates:
        raise ValueError("No fields to update — supply at least one argument")
    run_command(f"scontrol update job {shlex.quote(job_id)} {updates}")
    jobs = compute.get_statuses([job_id])
    if not jobs:
        raise ValueError(f"Job {job_id} not found after update")
    return jobs[0]


@mcp.tool()
def cancel_job(job_id: str, resource_id: str = RESOURCE_ID) -> Job | str:
    """Cancel a queued or running job and report its resulting state.
    (IRI: DELETE /compute/cancel/{resource_id}/{job_id})
    """
    _check_resource(resource_id)
    return compute.cancel(job_id)


# === filesystem ==============================================================
# Paths are relative to the home directory unless absolute.

@mcp.tool()
def fs_ls(path: str = ".", show_hidden: bool = False) -> str:
    """List a directory on the cluster. (IRI: GET /filesystem/ls)"""
    flags = "-la" if show_hidden else "-l"
    return run_command(f"ls {flags} {quote_path(path)}")


@mcp.tool()
def fs_stat(path: str) -> str:
    """Stat a file or directory on the cluster. (IRI: GET /filesystem/stat)"""
    return run_command(f"stat {quote_path(path)}")


@mcp.tool()
def fs_view(path: str) -> str:
    """Read a whole text file on the cluster (output capped at 200KB).
    (IRI: GET /filesystem/view) For large files use fs_head/fs_tail.
    """
    return run_command(f"cat {quote_path(path)}")


@mcp.tool()
def fs_head(path: str, lines: int = 50) -> str:
    """Read the first lines of a file on the cluster. (IRI: GET /filesystem/head)"""
    return run_command(f"head -n {int(lines)} {quote_path(path)}")


@mcp.tool()
def fs_tail(path: str, lines: int = 50) -> str:
    """Read the last lines of a file on the cluster — e.g. a job's
    slurm-<job_id>.out. (IRI: GET /filesystem/tail)
    """
    return run_command(f"tail -n {int(lines)} {quote_path(path)}")


@mcp.tool()
def fs_mkdir(path: str) -> str:
    """Create a directory (and parents) on the cluster. (IRI: POST /filesystem/mkdir)"""
    quoted = quote_path(path)
    return run_command(f"mkdir -p {quoted} && echo created: $(realpath {quoted})")


@mcp.tool()
def fs_upload(path: str, content: str, binary: bool = False) -> str:
    """Write a file on the cluster, creating parent directories.
    (IRI: POST /filesystem/upload — max 5 MB)

    For text files pass the content directly (binary=False, the default).
    For binary files pass the content as base64 and set binary=True; it will
    be decoded before writing. Use fs_compress + fs_download for files over 5 MB.
    """
    import base64 as _b64
    raw: str | bytes
    if binary:
        raw = _b64.b64decode(content)
    else:
        raw = content
    size = len(raw) if isinstance(raw, bytes) else len(raw.encode())
    if size > 5 * 1024 * 1024:
        raise ValueError(f"Content is {size:,} bytes — exceeds 5 MB upload limit.")
    abs_path = write_remote_file(path, raw)
    return f"Wrote {size:,} bytes to {abs_path}"


@mcp.tool()
def fs_checksum(path: str) -> str:
    """SHA-256 checksum of a file on the cluster. (IRI: GET /filesystem/checksum)"""
    return run_command(f"sha256sum {quote_path(path)}")


@mcp.tool()
def fs_download(path: str) -> str:
    """Download a small file from the cluster as base64. (IRI: GET /filesystem/download)

    Capped at 5 MB (matching IRI spec). Use fs_compress first for larger files,
    then download the archive. The caller can base64-decode and write locally.
    """
    size_out = run_command(f"stat -c %s {quote_path(path)}")
    size = int(size_out.strip())
    if size > 5 * 1024 * 1024:
        raise ValueError(
            f"File is {size:,} bytes — exceeds 5 MB limit. "
            f"Compress it first with fs_compress, or transfer with: "
            f"scp {config.ssh_host()}:{path} ."
        )
    return run_command(f"base64 {quote_path(path)}")


@mcp.tool()
def fs_cp(src: str, dst: str) -> str:
    """Copy a file or directory on the cluster. (IRI: POST /filesystem/cp)

    Uses cp -r so it works for both files and directories.
    """
    return run_command(f"cp -r {quote_path(src)} {quote_path(dst)} && echo ok")


@mcp.tool()
def fs_mv(src: str, dst: str) -> str:
    """Move or rename a file or directory on the cluster. (IRI: POST /filesystem/mv)

    Destructive — the source path will no longer exist after this call.
    """
    return run_command(f"mv {quote_path(src)} {quote_path(dst)} && echo ok")


@mcp.tool()
def fs_chmod(path: str, mode: str) -> str:
    """Change file permissions on the cluster. (IRI: PUT /filesystem/chmod)

    mode is an octal string, e.g. '755' or '644'.
    """
    return run_command(f"chmod {shlex.quote(mode)} {quote_path(path)} && echo ok")


@mcp.tool()
def fs_chown(path: str, owner: str = "", group: str = "") -> str:
    """Change file ownership on the cluster. (IRI: PUT /filesystem/chown)

    Supply owner, group, or both. Normal users can only change group to one
    they belong to; changing owner requires root.
    """
    if not owner and not group:
        raise ValueError("Provide at least one of owner or group")
    spec = owner + (":" + group if group else "")
    return run_command(f"chown {shlex.quote(spec)} {quote_path(path)} && echo ok")


@mcp.tool()
def fs_symlink(path: str, link_path: str) -> str:
    """Create a symbolic link on the cluster. (IRI: POST /filesystem/symlink)

    path is the target; link_path is the new symlink to create.
    """
    return run_command(
        f"ln -s {quote_path(path)} {quote_path(link_path)} && echo ok"
    )


_COMPRESSION_FLAGS = {
    CompressionType.NONE: "",
    CompressionType.GZIP: "z",
    CompressionType.BZIP2: "j",
    CompressionType.XZ: "J",
}


@mcp.tool()
def fs_compress(
    target_path: str,
    path: str | None = None,
    match_pattern: str | None = None,
    dereference: bool = False,
    compression: CompressionType = CompressionType.GZIP,
) -> str:
    """Create an archive on the cluster. (IRI: POST /filesystem/compress)

    target_path: path of the archive to create.
    path: source file or directory (defaults to current directory).
    match_pattern: regex passed to find -regex to filter files.
    dereference: follow symlinks (-h).
    compression: gzip (default), bzip2, xz, or none.
    """
    flag = _COMPRESSION_FLAGS[compression]
    deref = "h" if dereference else ""
    tar_flags = f"-{deref}c{flag}f"

    if match_pattern:
        src = quote_path(path or ".")
        pattern = shlex.quote(match_pattern)
        cmd = (
            f"find {src} -regex {pattern} -print0 | "
            f"tar {tar_flags} {quote_path(target_path)} --null -T -"
        )
    else:
        src = quote_path(path or ".")
        cmd = f"tar {tar_flags} {quote_path(target_path)} {src}"

    return run_command(cmd + " && echo ok")


@mcp.tool()
def fs_extract(
    path: str,
    target_path: str,
    compression: CompressionType = CompressionType.GZIP,
) -> str:
    """Extract an archive on the cluster. (IRI: POST /filesystem/extract)

    path: archive file to extract.
    target_path: directory to extract into (created if absent).
    compression: gzip (default), bzip2, xz, or none.
    """
    flag = _COMPRESSION_FLAGS[compression]
    tar_flags = f"-x{flag}f"
    return run_command(
        f"mkdir -p {quote_path(target_path)} && "
        f"tar {tar_flags} {quote_path(path)} -C {quote_path(target_path)} && echo ok"
    )


# === extensions (not part of the IRI API) ====================================

@mcp.tool()
def run_command_on_cluster(command: str) -> str:
    """Run an arbitrary shell command on the im login node (extension —
    not an IRI endpoint).

    Use only when no dedicated tool fits, e.g. 'module avail' to list software,
    'sinfo' for node state, 'squeue' for the queue, or 'sacct' for job history.
    Runs under a login shell from the home directory; returns stdout+stderr. Do
    not run heavy computation on the login node — submit a job instead.
    """
    return run_command(command)


def main():
    serve(mcp)


if __name__ == "__main__":
    main()
