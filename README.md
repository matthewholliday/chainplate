# Chainplate

Chainplate is an **XML-based markup language** for rapid development of **generative AI applications**, including chatbots, workflows, and agents.  

⚠️ **Pre-release Notice**: Chainplate is under active development and not yet production-ready. Expect breaking changes and incomplete features.

---

## 🚀 Features (Coming Soon)
- Define AI workflows using a simple XML-based DSL.  
- Rapidly prototype and deploy chatbots and AI agents.  
- Compose multi-step reasoning chains with minimal code.  

---

## 📦 Installation

Currently, Chainplate must be installed from source. Future releases will be available on **PyPI** and as a **Docker container**.

> **Note:** Chainplate currently only supports the **OpenAI API**. Support for **Claude**, **OpenLLaMA**, and custom extensions is coming soon.  
> You will need to set your `OPENAI_API_KEY` environment variable with a valid OpenAI API key.

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/chainplate.git
   cd chainplate
   ```

2. (Optional) Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux / macOS
   venv\Scripts\activate     # Windows
   ```

3. Build and install locally:
   ```bash
   python -m pip install build
   python -m build
   python -m pip install -e .
   ```

4. Set your OpenAI API key:
   ```bash
   export OPENAI_API_KEY=your_api_key_here   # Linux / macOS
   setx OPENAI_API_KEY "your_api_key_here"   # Windows
   ```

5. Test the installation:
   ```bash
   chainplate
   ```

---

## 🐳 Docker

A Docker image can be built locally to run the Chainplate server in a containerized environment.

### Build the image

Using Docker directly:
```powershell
# From repo root
docker build -t chainplate:latest .
```

Or with the provided PowerShell helper script:
```powershell
# Optional: set a custom Python version
$Env:CHAINPLATE_PYTHON = "3.11"

./scripts/build_docker.ps1 -ImageName chainplate -Tag latest
# With registry + push (example)
./scripts/build_docker.ps1 -ImageName chainplate -Registry ghcr.io/youruser -Tag v0.1.0 -Push
```

### Run the container

```powershell
# Basic run (ephemeral DB inside container)
docker run --rm -p 5000:5000 -e OPENAI_API_KEY=$Env:OPENAI_API_KEY chainplate:latest

# Persist database + logs to host volume
docker run --rm -p 5000:5000 -e OPENAI_API_KEY=$Env:OPENAI_API_KEY -v ${PWD}/data:/data chainplate:latest
```

### Environment variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `OPENAI_API_KEY` | Required for model calls | (none) |
| `CHAINPLATE_DB` | Path to sqlite DB inside container | `/data/chainplate.db` |
| `CHAINPLATE_PORT` | Port the Flask server binds to | `5000` |

Expose a different port:
```powershell
docker run --rm -e OPENAI_API_KEY=$Env:OPENAI_API_KEY -e CHAINPLATE_PORT=8080 -p 8080:8080 chainplate:latest
```

### Updating / Rebuilding
If you change source code, rebuild the image:
```powershell
docker build -t chainplate:latest .
```

---

## ⚡ Usage

Once installed, you can run workflows defined in XML files. For example, the repository includes a **Hello World** workflow:

```bash
chainplate --workflow examples/hello-world.xml
```

### Optional: Run the Development Server with CORS

If you are building a frontend (e.g. React/Vite) that calls Chainplate's Flask server from `http://localhost:3000` or similar, you can enable permissive CORS for local development:

```bash
set CHAINPLATE_ENABLE_CORS=true              # PowerShell: $Env:CHAINPLATE_ENABLE_CORS = "true"
set CHAINPLATE_CORS_ORIGINS=http://localhost:3000,http://localhost:5173  # Comma-separated list (optional)
```

Then start your server mode (example command depends on how you invoke it). By default the following origins are allowed when CORS is enabled and no override is provided:

```
http://localhost:3000
http://127.0.0.1:3000
http://localhost:5173
http://127.0.0.1:5173
http://localhost:8000
http://127.0.0.1:8000
```

Use these variables only for local development; avoid enabling broad CORS in production deployments.

### Example: `examples/hello-world.xml`

```xml
<pipeline name="Send Prompt Example">
    <context>
        Reply to everything in the silliest way possible.
        <send-prompt output_var="response" content="What is the capital of France?" />
    </context>
    <debug>The response is: {{response}}</debug>
    <set-variable name="__chat_output__">{{ response }}</set-variable>
</pipeline>
```

This pipeline:
1. Defines a **context** (“Reply to everything in the silliest way possible”).  
2. Sends a **prompt** to the model (`What is the capital of France?`) and stores the output in a variable `response`.  
3. Prints the response with `<debug>`.  
4. Sets the special variable `__chat_output__` so the final output can be captured.  

---

## 📄 Pre-release Specification

You can view the **pre-release Chainplate specification** [here](https://example.com/chainplate-spec).

## 🛣️ Future Plans

The roadmap for Chainplate includes:  

- **Modes**  
  - Workflow mode (currently functional)  
  - Chat mode (currently functional)  
  - Agent mode (planned)  

- **Core Goals**  
  - Publish a stable, versioned specification for production use  
  - Distribute via **PyPI** and **Docker**  
  - Provide open-source contribution guidelines and a developer starter kit  

- **New XML Elements (Planned)**  
  - `<rest-server>`: Launch a REST API for programmatic integration  
  - Built-in developer server and editor UI  
  - `<mcp>`: Define MCP tools usable within a given scope  
  - `<get-sentiment>`: Extract sentiment from text  
  - `<get-collection>`: Retrieve structured collections from text  
  - Support for **Claude AI**, **OpenLLaMA**, and **OpenAI-format-compatible services**  

---

## 🤝 Contributing

At this stage, the best way to contribute is by:  
- **Testing** workflows and features.  
- **Submitting issues** for bugs, unexpected behavior, or feature requests.  

Once the **extensions system** reaches a stable release, contributions from developers (PRs, plugins, new elements) will be welcomed.  

---

## 📜 License

This project is licensed under the [MIT License](LICENSE).

