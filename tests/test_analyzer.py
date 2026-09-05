import json
import pytest
from unittest.mock import patch, MagicMock
from ops_hardener.core.analyzer import analyze_file, _extract_json
from ops_hardener.schemas.audit import AuditReport

# ---------------------------------------------------------------------------
# Helpers to build a mock streaming response that matches litellm's shape
# when stream=True.
# ---------------------------------------------------------------------------

_PAYLOAD = json.dumps({
    "file_type": "Dockerfile",
    "score": 85,
    "findings": [],
    "hardened_code": "FROM ubuntu:22.04",
})


def _make_stream_chunk(content: str):
    """Return a minimal object that looks like a litellm streaming chunk."""
    delta = MagicMock()
    delta.content = content
    choice = MagicMock()
    choice.delta = delta
    chunk = MagicMock()
    chunk.choices = [choice]
    return chunk


def _make_stream(payload: str):
    """Split payload across multiple chunks to simulate real streaming."""
    mid = len(payload) // 2
    return iter([
        _make_stream_chunk(payload[:mid]),
        _make_stream_chunk(payload[mid:]),
    ])


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@patch("ops_hardener.core.analyzer.completion")
def test_analyze_file_happy_path(mock_completion):
    """analyze_file assembles streamed chunks and returns a valid AuditReport."""
    mock_completion.return_value = _make_stream(_PAYLOAD)

    report = analyze_file("FROM ubuntu:latest", "Dockerfile", model="test-model")

    assert isinstance(report, AuditReport)
    assert report.score == 85
    assert report.hardened_code == "FROM ubuntu:22.04"
    assert len(report.findings) == 0


@patch("ops_hardener.core.analyzer.completion")
def test_analyze_file_strips_markdown_fence(mock_completion):
    """analyze_file correctly strips ```json ... ``` wrapping from LLM output."""
    fenced = f"```json\n{_PAYLOAD}\n```"
    mock_completion.return_value = _make_stream(fenced)

    report = analyze_file("FROM ubuntu:latest", "Dockerfile", model="test-model")
    assert report.score == 85


@patch("ops_hardener.core.analyzer.completion")
def test_analyze_file_api_failure_raises_runtime_error(mock_completion):
    """A failure during the completion() call raises RuntimeError."""
    mock_completion.side_effect = Exception("network timeout")

    with pytest.raises(RuntimeError, match="LLM API call failed"):
        analyze_file("FROM ubuntu:latest", "Dockerfile", model="test-model")


@patch("ops_hardener.core.analyzer.completion")
def test_analyze_file_bad_json_raises_value_error(mock_completion):
    """Invalid JSON from the LLM raises ValueError, not a bare json.JSONDecodeError."""
    mock_completion.return_value = _make_stream("not valid json at all")

    with pytest.raises(ValueError, match="invalid JSON"):
        analyze_file("FROM ubuntu:latest", "Dockerfile", model="test-model")


@patch("ops_hardener.core.analyzer.completion")
def test_analyze_file_schema_mismatch_raises_value_error(mock_completion):
    """JSON that doesn't match AuditReport schema raises ValueError."""
    bad_schema = json.dumps({"wrong_field": 123})
    mock_completion.return_value = _make_stream(bad_schema)

    with pytest.raises(ValueError, match="did not match the expected schema"):
        analyze_file("FROM ubuntu:latest", "Dockerfile", model="test-model")


# ---------------------------------------------------------------------------
# _extract_json unit tests (pure function, no mocking needed)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("raw,expected", [
    ('```json\n{"a":1}\n```', '{"a":1}'),
    ('```\n{"a":1}\n```', '{"a":1}'),
    ('```yaml\n{"a":1}\n```', '{"a":1}'),
    ('  ```json\n{"a":1}\n```  ', '{"a":1}'),
    ('{"a":1}', '{"a":1}'),          # no fence — returned as-is
])
def test_extract_json(raw, expected):
    assert _extract_json(raw) == expected
