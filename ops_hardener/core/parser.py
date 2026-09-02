import yaml
from pathlib import Path
from typing import Dict, Any

def parse_file(file_path: Path) -> Dict[str, Any]:
    """
    Validates and parses a Dockerfile or Kubernetes YAML manifest.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    content = file_path.read_text(encoding="utf-8")
    file_type = detect_file_type(file_path, content)

    if file_type == "UNKNOWN":
        raise ValueError("Unsupported file type. Please provide a Dockerfile or Kubernetes YAML manifest.")
        
    if file_type == "Kubernetes YAML":
        try:
            # Validate it's proper YAML and handle multi-document manifests
            list(yaml.safe_load_all(content))
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid Kubernetes YAML manifest: {e}")

    return {
        "file_path": str(file_path),
        "file_type": file_type,
        "content": content,
    }

def detect_file_type(file_path: Path, content: str) -> str:
    """
    Detects whether the file is a Dockerfile or Kubernetes YAML.
    """
    file_name = file_path.name.lower()

    if "dockerfile" in file_name or content.startswith("FROM "):
        return "Dockerfile"

    if file_name.endswith(".yaml") or file_name.endswith(".yml"):
        if "apiVersion:" in content and "kind:" in content:
            return "Kubernetes YAML"

    return "UNKNOWN"
