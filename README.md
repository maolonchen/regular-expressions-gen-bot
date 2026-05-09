# RegAgent - LLM-Powered Regex Generation Service

RegAgent is an intelligent regular expression generation service powered by Large Language Models. It accepts natural language descriptions of pattern-matching needs, iteratively generates and refines regex patterns, and validates them against sample inputs until correct results are achieved.

## Features

- **Natural Language to Regex**: Describe what you want to match in plain language
- **Iterative Refinement**: Automatically corrects failed regexes through up to 20 rounds of LLM feedback
- **Multi-Sample Validation**: Supports primary samples, additional examples, and negative examples
- **Safety Controls**: Execution timeout, regex length limits, and match count caps
- **LLM-Agnostic**: Works with any OpenAI-compatible chat completions API
- **High Accuracy**: Achieves **92%+ accuracy** across 63 test cases covering 13+ categories

## Architecture

```
User Request (NL + samples)
        │
        ▼
   ┌─────────────┐
   │  LLM Call   │ ◄── Generate initial regex
   └──────┬──────┘
          │
          ▼
   ┌─────────────┐
   │  Validate   │ ◄── Test against sample input via re.finditer
   └──────┬──────┘
          │
    ┌─────┴─────┐
    │ Correct?  │
    └─────┬─────┘
     No   │   Yes
     │    │    │
     ▼    │    ▼
  Error   │  Final Check ──► LLM confirms
  Report  │                    │
     │    │              ┌────┴────┐
     └────►├──────────► │ CORRECT │ ──► Return
           │             └─────────┘
           ▼
      Retry (up to 20 attempts)
```

## Quick Start

### Prerequisites

- Python >= 3.8 (tested on 3.13)
- [uv](https://docs.astral.sh/uv/) package manager

### Installation

```bash
# Clone the repository
git clone <repo-url>
cd reg_agent_dev

# Install dependencies
uv sync
```

### Configuration

Set the following environment variables before running:

| Variable | Required | Default | Description |
|---|---|---|---|
| `CHAT_MODEL_NAME` | Yes | - | LLM model name |
| `CHAT_MODEL_API_URL` | Yes | - | OpenAI-compatible API endpoint |
| `CHAT_API_KEY` | Yes | - | API key |
| `API_HOST` | No | `0.0.0.0` | Server bind address |
| `API_PORT` | No | `8765` | Server bind port |
| `MAX_CORRECTION_ATTEMPTS` | No | `20` | Max refinement rounds |
| `MAX_EXECUTION_TIME` | No | `1.0` | Regex validation timeout (seconds) |
| `MAX_REGEX_LENGTH` | No | `1000` | Max regex length (chars) |
| `DEBUG` | No | `false` | Enable debug logging |

### Running

```bash
# Start via script
python run_server.py

# Or use the management tool
chmod +x manage.sh
./manage.sh start
./manage.sh status
./manage.sh logs
./manage.sh stop
```

## API Reference

### Generate Regex

```
POST /generate-regex
```

**Request Body:**

```json
{
  "user_request": "Extract all email addresses",
  "sample_input": "Contact us at support@example.com or sales@company.org",
  "expected_matches": ["support@example.com", "sales@company.org"],
  "additional_examples": ["Optional: more example strings"],
  "negative_examples": ["Optional: strings that should NOT match"]
}
```

**Response (Success):**

```json
{
  "success": true,
  "regex": "[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}",
  "matches": ["support@example.com", "sales@company.org"],
  "attempts": 3,
  "error": null
}
```

**Response (Failure):**

```json
{
  "success": false,
  "regex": "",
  "matches": [],
  "attempts": 20,
  "error": "Failed to generate correct regex after 20 attempts"
}
```

### Health Check

```
GET /health
```

Returns `{"status": "healthy", "llm_provider": "<model name>"}`.

## Benchmark

Run the accuracy benchmark:

```bash
python scripts/test_accuracy.py
```

This evaluates 63 test cases across categories including emails, phone numbers, dates, IPv4 addresses, URLs, credit card numbers, hex colors, hashtags, floating-point numbers, and more.

## Project Structure

```
reg_agent_dev/
├── main.py                  # FastAPI application entry point
├── run_server.py            # Uvicorn server launcher
├── manage.sh                # Service lifecycle management script
├── pyproject.toml           # Dependencies and project metadata
├── app/
│   ├── algorithms/
│   │   └── regex_agent.py   # Core: iterative regex generation agent
│   ├── api/
│   │   └── llm_api.py       # LLM API client (OpenAI-compatible)
│   ├── conf/
│   │   ├── config.py        # Environment-based configuration
│   │   └── prompts.py       # Prompt templates (gitignored)
│   ├── schemas/
│   │   └── re_schemas.py    # Pydantic request/response models
│   └── utils/
│       └── log_utils.py     # Logging with console + file output
├── scripts/
│   └── test_accuracy.py     # Accuracy benchmark script
└── data/
    └── test_data.json       # 63 test cases (13+ categories)
```

## License

MIT
