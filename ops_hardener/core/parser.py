import re
import yaml
from pathlib import Path
from typing import Any, Dict

_DOCKERFILE_CONTENT_RE = re.compile(
    r"^\s*(?:#\s*\S.*\n)*\s*(?:FROM|ARG)\s",
    re.IGNORECASE | re.MULTILINE,
)

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

    if "dockerfile" in file_name or _DOCKERFILE_CONTENT_RE.search(content):
        return "Dockerfile"

    if file_name.endswith((".yaml", ".yml")):
        if _K8S_API_VERSION_RE.search(content) and _K8S_KIND_RE.search(content):
            return "Kubernetes YAML"

    return "UNKNOWN"
