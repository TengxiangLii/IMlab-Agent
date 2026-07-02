"""Configuration for the imlab MCP servers.

Settings come from, in order of precedence:
  1. Environment variables (IMLAB_*)
  2. The user config file ~/.imlab/config.json (path override: IMLAB_CONFIG)
  3. Defaults

The config file is created with the help of the `imlab-configuring` skill:

    {
      "ssh": {"host": "imlab"}
    }

`ssh.host` is an alias from ~/.ssh/config or a plain user@hostname; key-based
auth is assumed (no credentials are stored here). The `im` cluster does not
enforce Slurm accounting, so no project/account is required to submit — an
`account` may be given per job but there is no default and no billing.

Documentation search ships as a BM25 keyword index by default: the `im` cluster
is a small local machine with no embedding endpoint. EMBED_BASE_URL / EMBED_MODEL
are overridable constants — point them at an embedding endpoint and rebuild the
index (rag.ingest) to enable semantic search.
"""
import json
import os
from contextlib import ExitStack
from functools import lru_cache
from importlib import resources
from pathlib import Path

CONFIG_PATH = Path(os.environ.get("IMLAB_CONFIG", "~/.imlab/config.json")).expanduser()


def _file_config() -> dict:
    """The parsed config file, or {} if absent. Raises on malformed JSON."""
    try:
        with open(CONFIG_PATH) as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Malformed config file {CONFIG_PATH}: {e}") from e


def ssh_host() -> str:
    """SSH destination for the im cluster (alias or user@hostname).

    The default `imlab` is an alias the `imlab-configuring` skill adds to
    ~/.ssh/config (→ 131.112.104.58, directly on-campus or via a ProxyJump
    through the TSUBAME login node off-campus).
    """
    return (os.environ.get("IMLAB_HOST")
            or _file_config().get("ssh", {}).get("host")
            or "imlab")


def default_account() -> str | None:
    """Optional Slurm account (the sbatch --account) for jobs that don't set one.

    The `im` cluster runs with AccountingStorageEnforce=none, so an account is
    NOT required to submit. This returns a value only if the user configured one
    (env IMLAB_ACCOUNT or `account` in the config file); otherwise None and no
    --account is emitted.
    """
    return (os.environ.get("IMLAB_ACCOUNT")
            or _file_config().get("account")
            or None)


# --- Embedding endpoint -----------------------------------------------------
# The im cluster ships a BM25-only docs index (no embeddings.npy), so these
# constants are empty by default and docs search uses keyword matching. To enable
# semantic search, set them to a reachable endpoint + model and rebuild the index
# with `python -m imlab_mcp.rag.ingest` (a committed embeddings.npy is tied to the
# exact model, so the model must not change between ingest and query time).

EMBED_BASE_URL = ""
EMBED_MODEL = ""


def embed_api_key() -> str:
    """API key for the embedding endpoint (the only user-configurable embedding setting).

    Resolved in order: IMLAB_EMBED_API_KEY, then embedding.api_key in the config
    file. Empty string means no auth header is sent — and with no configured
    endpoint, docs search stays on BM25.
    """
    file = _file_config().get("embedding", {})
    return (os.environ.get("IMLAB_EMBED_API_KEY")
            or file.get("api_key") or "")


# --- Static data ------------------------------------------------------------

_RESOURCE_STACK = ExitStack()


def _bundled_data_dir() -> Path:
    """Filesystem path to package data, including zip-safe extraction fallback."""
    data = resources.files("imlab_mcp") / "data"
    return _RESOURCE_STACK.enter_context(resources.as_file(data))


_DATA_DIR = _bundled_data_dir()

DOCS_INDEX_DIR = Path(os.environ.get("IMLAB_DOCS_INDEX", _DATA_DIR / "docs_index"))
# The documentation source is our own original packaged guide — facts in our own
# words — so it is committed and the index can be freely distributed. `rag.ingest`
# chunks it by heading.
DOCS_SOURCE = Path(os.environ.get("IMLAB_DOCS_SOURCE", _DATA_DIR / "imlab_guide.md"))
DOCS_SITE_BASE = "internal://imlab/"  # no public portal; guide is self-contained


@lru_cache(maxsize=1)
def load_cluster_config() -> dict:
    """Load the static im-cluster description (nodes, partitions, modules, storage)."""
    path = Path(os.environ.get("IMLAB_CLUSTER_CONFIG", _DATA_DIR / "imlab_config.json"))
    with open(path) as f:
        return json.load(f)
