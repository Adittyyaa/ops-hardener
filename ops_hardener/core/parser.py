import re
import yaml
from pathlib import Path
from typing import Any, Dict

# ---------------------------------------------------------------------------
# Dockerfile detection
# ---------------------------------------------------------------------------
# A Dockerfile may begin with one or more BuildKit syntax/escape directives
# before the first real instruction, e.g.:
#   # syntax=docker/dockerfile:1
#   # escape=`
#   FROM ubuntu:22.04
# The original `content.startswith("FROM ")` check missed these files entirely.
_DOCKERFILE_CONTENT_RE = re.compile(
    r"^\s*(?:#\s*\S.*\n)*\s*FROM\s",
    re.IGNORECASE | re.MULTILINE,
)

# ---------------------------------------------------------------------------
# Kubernetes YAML detection
# ---------------------------------------------------------------------------
# Raw substring search (`"apiVersion:" in content`) would match a string
# inside a comment or a quoted value.  We use a regex that requires the key
# to appear at the start of a line (possibly after "---" document separators).
_K8S_API_VERSION_RE = re.compile(r"^apiVersion\s*:", re.MULTILINE)
_K8S_KIND_RE = re.compile(r"^kind\s*:", re.MULTILINE)


def parse_file(file_path: Path) -> Dict[str, Any]:
    """Validate and parse a Dockerfile or Kubernetes YAML manifest.

    Returns a dict with keys ``file_path``, ``file_type``, and ``content``.

    Raises
    ------
    FileNotFoundError
        If *file_path* does not exist (guards programmatic callers; Typer's
        ``exists=True`` covers the CLI path).
    ValueError
        If the file type cannot be determined or the YAML is malformed.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    content = file_path.read_text(encoding="utf-8")
    file_type = detect_file_type(file_path, content)

    if file_type == "UNKNOWN":
        raise ValueError(
            "Unsupported file type. Please provide a Dockerfile or a Kubernetes YAML manifest."
        )

    if file_type == "Kubernetes YAML":
        try:
            # Validate syntax and handle multi-document manifests (--- separated).
            list(yaml.safe_load_all(content))
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid Kubernetes YAML manifest: {e}") from e

    return {
        "file_path": str(file_path),
        "file_type": file_type,
        "content": content,
    }


def detect_file_type(file_path: Path, content: str) -> str:
    """Return ``"Dockerfile"``, ``"Kubernetes YAML"``, or ``"UNKNOWN"``."""
    file_name = file_path.name.lower()

    # --- Dockerfile ---
    # Match by filename convention OR by content pattern (handles BuildKit
    # syntax/escape directive comments that precede the first FROM instruction).
    if "dockerfile" in file_name or _DOCKERFILE_CONTENT_RE.search(content):
        return "Dockerfile"

    # --- Kubernetes YAML ---
    # Only consider files with a YAML extension, then require both apiVersion
    # and kind to appear as top-level keys (start of line), not inside values
    # or comments.
    if file_name.endswith((".yaml", ".yml")):
        if _K8S_API_VERSION_RE.search(content) and _K8S_KIND_RE.search(content):
            return "Kubernetes YAML"

    return "UNKNOWN"
