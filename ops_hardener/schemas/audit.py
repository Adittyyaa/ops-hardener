from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class Severity(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class Finding(BaseModel):
    severity: Severity = Field(..., description="The severity of the finding.")
    rule_id: str = Field(..., description="A unique identifier for the rule violated.")
    issue: str = Field(..., description="A short summary of the issue.")
    description: str = Field(..., description="Detailed description of the vulnerability or anti-pattern.")
    recommendation: str = Field(..., description="How to fix the issue.")
    line_number: Optional[int] = Field(None, description="The line number where the issue was found, if applicable.")


class AuditReport(BaseModel):
    file_type: str = Field(..., description="The type of the file analyzed (e.g., Dockerfile, Kubernetes YAML).")
    score: int = Field(..., ge=0, le=100, description="An overall security score from 0 to 100.")
    findings: List[Finding] = Field(default_factory=list, description="List of security and best-practice findings.")
    # Optional so that a valid audit report can be returned even if the LLM
    # omits or fails to produce hardened code.  --diff and --fix both check
    # for None before operating on this field.
    hardened_code: Optional[str] = Field(
        None,
        description="The full, hardened version of the input file following best practices.",
    )
