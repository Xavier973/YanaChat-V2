# YanaChat V2

Mistral-powered chatbot with FastAPI and JSONL audit logging.

## Quick Start

### 1. Setup Environment

```bash
# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Credentials

```bash
# Copy the example file
copy .env.example .env

# Edit .env with your Mistral API credentials
# MISTRAL_API_KEY=your_key_here
# MISTRAL_API_URL=https://api.mistral.ai/v1/chat/completions
```

### 3. Run Locally

```bash
# Start the API
uvicorn app.main:app --reload --port 8000

# Open in browser
# http://localhost:8000
```

### 4. Run Tests

```bash
python tests/run_tests.py
```

## Docker

```bash
# Build and run
docker compose up --build

# View logs
docker compose logs -f api
```

## API Endpoints

### Chat Endpoint
```bash
POST /api/chat
Content-Type: application/json

{
    "query": "Your question here",
    "session_id": "optional-user-id"
}

# Response
{
    "response": "Mistral's answer here"
}
```

### Health Check
```bash
GET /health

# Response
{
    "status": "ok",
    "service": "YanaChat V2"
}
```

## Project Structure

```
YanaChat_V2/
├── app/
│   ├── main.py              # FastAPI application
│   └── static/
│       └── index.html       # Web UI
├── src/
│   ├── llm_pipeline.py      # Mistral API wrapper
│   ├── chat_handler.py      # Orchestration & logging
│   └── __init__.py
├── logs/
│   └── interactions.jsonl   # Audit log (append-only)
├── tests/
│   └── run_tests.py         # Integration tests
├── .env                     # Secrets (git-ignored)
├── .env.example             # Example configuration
├── requirements.txt         # Python dependencies
├── docker-compose.yml       # Docker configuration
├── Dockerfile               # Container image
└── README.md               # This file
```

## Key Features

- **Mistral LLM Integration**: Uses Mistral's latest API for high-quality responses
- **Robust Retry Logic**: Exponential backoff with 60-second timeout
- **JSONL Audit Logging**: Every interaction is logged for audit and improvement
- **Session Tracking**: Optional session IDs to group user queries
- **FastAPI Framework**: Modern, fast, async-capable web framework
- **Web UI**: Simple, responsive chat interface

## Configuration

### Environment Variables

```env
MISTRAL_API_KEY=your_api_key_here
MISTRAL_API_URL=https://api.mistral.ai/v1/chat/completions
PORT=8000
```

## Logging

Interactions are logged to `logs/interactions.jsonl` in JSONL format (one JSON object per line).

Example log entry:
```json
{
    "timestamp": "2026-01-22T20:11:04.555579",
    "session_id": "user123",
    "model": "mistral-large-latest",
    "query": "What is the capital of France?",
    "response": "The capital of France is Paris...",
    "latency_ms": 2340
}
```

## Development

### Adding Features

1. Modify components in `src/` or `app/`
2. Run tests: `python tests/run_tests.py`
3. Test locally: `uvicorn app.main:app --reload`

### Extending the LLM Pipeline

Edit `src/llm_pipeline.py`:
- Change model: modify `self.model = "..."`
- Adjust prompt: edit `system_prompt`
- Configure temperature: modify the JSON payload

### Viewing Logs

```powershell
# Last 10 entries
Get-Content logs/interactions.jsonl | ConvertFrom-Json -Stream | Select-Object -Last 10

# Parse and pretty-print
Get-Content logs/interactions.jsonl | ConvertFrom-Json -Stream | ConvertTo-Json
```

## Troubleshooting

### Import Errors
- Ensure `.venv/Scripts/activate` is run before executing Python
- Run `pip install -r requirements.txt` in the venv

### API Key Errors
- Check that `.env` contains `MISTRAL_API_KEY` and `MISTRAL_API_URL`
- Verify keys are valid on the Mistral console

### Timeout Errors
- Mistral API can be slow; default timeout is 60 seconds
- Check network connectivity
- Retry is automatic with exponential backoff

### Web Search Sources Not Logged
- **Known limitation**: Mistral Conversations API doesn't expose web_search sources
- See [`LIMITATIONS.md`](LIMITATIONS.md) for details and workarounds
- The `sources` field in logs will always be empty `[]` with current API

## License

MIT
