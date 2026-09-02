import json
import os
from dotenv import load_dotenv
from litellm import completion
from ops_hardener.schemas.audit import AuditReport

load_dotenv()

SYSTEM_PROMPT = """You are an expert Principal DevOps and Security Engineer.
Your task is to analyze Dockerfiles and Kubernetes YAML manifests for security vulnerabilities, misconfigurations, and performance anti-patterns.
You must return your analysis as a strict JSON object that conforms exactly to the following Pydantic schema:

{schema}

Ensure that the JSON output is completely valid and does not contain any markdown wrapping like ```json.
The 'hardened_code' field should contain the complete rewritten file applying all your recommendations.
"""

def analyze_file(file_content: str, file_type: str, model: str = "gpt-4o") -> AuditReport:
    """
    Sends the file content to an LLM for security auditing and parses the response.
    """
    schema_json = AuditReport.model_json_schema()
    prompt = SYSTEM_PROMPT.format(schema=json.dumps(schema_json, indent=2))
    
    try:
        response = completion(
            model=model,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"Analyze the following {file_type}:\n\n{file_content}"}
            ],
            response_format={"type": "json_object"}
        )
        
        raw_output = response.choices[0].message.content
        
        # Clean up markdown if the model still returns it despite instructions
        if raw_output.startswith("```json"):
            raw_output = raw_output[7:-3].strip()
        elif raw_output.startswith("```"):
            raw_output = raw_output[3:-3].strip()
            
        report_data = json.loads(raw_output)
        return AuditReport.model_validate(report_data)
        
    except Exception as e:
        raise RuntimeError(f"Failed to analyze file with LLM: {str(e)}")
