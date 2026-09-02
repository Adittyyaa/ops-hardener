import pytest
from pathlib import Path
from ops_hardener.core.parser import parse_file, detect_file_type

def test_detect_dockerfile(tmp_path: Path):
    file = tmp_path / "Dockerfile"
    file.write_text("FROM ubuntu:latest\nRUN echo 'hello'")
    assert detect_file_type(file, file.read_text()) == "Dockerfile"

def test_detect_kubernetes_yaml(tmp_path: Path):
    file = tmp_path / "deployment.yaml"
    content = """
apiVersion: apps/v1
kind: Deployment
metadata:
  name: test
"""
    file.write_text(content)
    assert detect_file_type(file, content) == "Kubernetes YAML"

def test_parse_file_unsupported(tmp_path: Path):
    file = tmp_path / "random.txt"
    file.write_text("Just some random text")
    with pytest.raises(ValueError, match="Unsupported file type"):
        parse_file(file)
