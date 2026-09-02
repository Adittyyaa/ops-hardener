import pytest
from unittest.mock import patch
from ops_hardener.core.analyzer import analyze_file
from ops_hardener.schemas.audit import AuditReport

@patch("ops_hardener.core.analyzer.completion")
def test_analyze_file(mock_completion):
    mock_response = type('Response', (), {
        'choices': [
            type('Choice', (), {
                'message': type('Message', (), {
                    'content': '{"file_type": "Dockerfile", "score": 85, "findings": [], "hardened_code": "FROM ubuntu:22.04"}'
                })()
            })()
        ]
    })()
    mock_completion.return_value = mock_response

    report = analyze_file("FROM ubuntu:latest", "Dockerfile", model="test-model")
    
    assert isinstance(report, AuditReport)
    assert report.score == 85
    assert report.hardened_code == "FROM ubuntu:22.04"
    assert len(report.findings) == 0
