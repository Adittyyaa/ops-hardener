# ops-hardener 🛡️

**ops-hardener** is an intelligent CLI tool that scans your Dockerfiles and Kubernetes YAML manifests for security vulnerabilities, misconfigurations, and performance anti-patterns. 

Unlike traditional linters, it uses an LLM to not only detect issues, but to instantly generate a fully hardened, best-practice version of your code.

## How it works

1. **Ingestion:** Run the CLI against a file. It automatically detects whether it's a Dockerfile or a Kubernetes YAML manifest.
2. **Analysis:** The file is securely passed to an LLM (using the `litellm` router, which supports Groq, OpenAI, or local Ollama). The LLM acts as an expert DevOps engineer, scanning for things like running as root, missing CPU limits, or `privileged: true` flags.
3. **Structured Reporting:** It returns a strict JSON report which is converted into a beautiful, color-coded terminal UI, complete with a Security Grade (A-F).
4. **Auto-Fix (Optional):** Use the `--fix` flag to automatically write the LLM's hardened code to a new file, or `--diff` to see a side-by-side terminal diff of the proposed changes.

## Quick Start

```bash
# 1. Install
pip install -e .

# 2. Add your API key to a .env file (e.g., GROQ_API_KEY=your_key)
echo "GROQ_API_KEY=your_key" > .env

# 3. Scan a file!
ops-hardener scan Dockerfile
```

## Powerful Flags
- **`--model`**: Change the underlying LLM (e.g., `--model groq/llama-3.1-8b-instant`).
- **`--diff`**: View a beautiful, color-coded unified diff of the suggested changes in your terminal.
- **`--fix`**: Automatically save the hardened version to `<filename>.hardened`.
