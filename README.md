# ops-hardener 🛡️

A powerful, LLM-driven CLI tool that scans Dockerfiles and Kubernetes YAML manifests for security vulnerabilities, misconfigurations, and performance anti-patterns.

It not only flags issues but also generates a completely hardened, best-practice version of your file automatically!

## Features

- 🐳 **Dockerfile & K8s Support:** Automatically detects the file type and applies appropriate security context rules.
- 🧠 **LLM Powered:** Uses the LiteLLM router, allowing you to seamlessly switch between OpenAI, Groq, or local Ollama models.
- 💅 **Rich Terminal UI:** Beautiful color-coded tables, scores, and loading spinners.
- 🛠️ **Auto-Fix:** Automatically write hardened code to a new file using the `--fix` flag.
- 🔍 **Diff Viewer:** Preview LLM changes directly in your terminal using the `--diff` flag.

## Installation

1. Clone the repository and navigate into it:
   ```bash
   git clone https://github.com/YourUsername/ops-hardener.git
   cd ops-hardener
   ```
2. Create a virtual environment and install the CLI:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -e .
   ```
3. Set up your API key in a `.env` file in the root directory:
   ```env
   # For Groq
   GROQ_API_KEY=your_key_here
   
   # Or for OpenAI
   OPENAI_API_KEY=your_key_here
   
   # Or for local Ollama
   OLLAMA_HOST=http://localhost:11434
   ```

## Usage

Run a basic scan:
```bash
ops-hardener scan Dockerfile
```

Specify a custom model (Defaults to `gpt-4o`):
```bash
ops-hardener scan deployment.yaml --model groq/llama-3.1-8b-instant
```

View the proposed changes side-by-side:
```bash
ops-hardener scan Dockerfile --diff
```

Automatically write the hardened code to a new file:
```bash
ops-hardener scan Dockerfile --fix
```

## Security Rules Enforced

**Dockerfiles:**
- Prohibition of root user execution.
- Missing multi-stage builds.
- Floating image tags (e.g., `latest`).

**Kubernetes:**
- Prohibition of `privileged: true`.
- Missing `readinessProbe` and `livenessProbe`.
- Missing CPU/Memory requests and limits.
- Enforcing `readOnlyRootFilesystem: true`.

## Testing
To run the test suite:
```bash
pip install -e .[dev]
pytest
```
