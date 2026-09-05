import json
import re
from litellm import completion
from ops_hardener.schemas.audit import AuditReport

_SCHEMA_JSON: str = json.dumps(AuditReport.model_json_schema(), indent=2)

SYSTEM_PROMPT: str = f"""You are an expert Principal DevOps and Security Engineer.
Your task is to analyze Dockerfiles and Kubernetes YAML manifests for security vulnerabilities, misconfigurations, and performance anti-patterns.

For Dockerfiles, ensure best practices such as avoiding 'latest' tags, not running as root, and using multi-stage builds.

For Kubernetes manifests, strictly enforce the following checks:
- Containers running with 'privileged: true' are prohibited.
- Missing 'readinessProbe' and 'livenessProbe' are flagged.
- Missing 'resources.limits' and 'resources.requests' are flagged.
- Missing 'readOnlyRootFilesystem: true' in securityContexts is flagged.

You must return your analysis as a strict JSON object that conforms exactly to the following Pydantic schema:

{_SCHEMA_JSON}

Ensure that the JSON output is completely valid and does not contain any markdown wrapping like ```json.
The 'hardened_code' field should contain the complete rewritten file applying all your recommendations.
"""

def _extract_json(raw: str) -> str:
    """Return the JSON payload from raw, stripping markdown fences if present."""
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", raw, re.DOTALL)
    if match:
        return match.group(1).strip()
    return raw.strip()


def analyze_file(file_content: str, file_type: str, model: str = "gpt-4o") -> AuditReport:
    """Send *file_content* to an LLM for security auditing and return a validated AuditReport.

    Raises
    ------
    ValueError
        When the LLM returns JSON that does not conform to the AuditReport schema.
    RuntimeError
        When the LLM API call itself fails (network error, auth error, etc.).
    """
    # Stream the response so the caller's progress indicator stays alive and
    # the user sees activity rather than a frozen terminal on long responses.
    try:
        stream = completion(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Analyze the following {file_type}:\n\n{file_content}"},
            ],
            response_format={"type": "json_object"},
            stream=True,
        )
    except Exception as e:
        raise RuntimeError(f"LLM API call failed: {e}") from e

    try:
        raw_output = "".join(chunk.choices[0].delta.content or "" for chunk in stream)
    except Exception as e:
        raise RuntimeError(f"Error while reading LLM stream: {e}") from e

    json_text = _extract_json(raw_output)

    try:
        report_data = json.loads(json_text)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"LLM returned invalid JSON (parse error: {e}).\n"
            f"Raw output (first 500 chars): {raw_output[:500]!r}"
        ) from e

    try:
        return AuditReport.model_validate(report_data)
    except Exception as e:
        raise ValueError(f"LLM response did not match the expected schema: {e}") from e
