# Gemini Codebase Agent

A small codebase agent with a JavaScript version and a beginner-friendly
Python version. It uses the Gemini API with three read-only tools:

- `list_files` — inspect folders and files
- `read_file` — read a file, capped at 8,000 characters
- `search_code` — search supported source and documentation files

The model chooses which tool to call. The script executes it locally, returns
the result to the model, and repeats until the model has enough evidence to
answer.

## Requirements

- Node.js 18 or later (Node 24 is supported)
- A Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey)

## Setup

Install the SDK:

```bash
npm install @google/genai
# or, for the Python version:
python3 -m pip install google-genai
```

Set one of these environment variables. `GEMINI_API_KEY` takes precedence.

```bash
export GEMINI_API_KEY="your-api-key"
# or
export GOOGLE_API_KEY="your-api-key"
```

Do not commit API keys to the repository.

## Run

Ask a question as the first argument:

```bash
node agent-gemini.mjs "how does this project work?"
node agent-gemini.mjs "where is API authentication handled?"
# Python equivalent:
python3 agent_gemini.py "how does this project work?"
```

Run the command from the repository you want the agent to inspect. The agent
uses the current working directory as its codebase root.

## Models

The simple Python agent uses `gemini-3.5-flash` by default. Choose a different
model without editing code:

```bash
export GEMINI_MODEL="gemini-3.7-flash"
python3 agent_gemini.py "how does this project work?"
```

### JavaScript fallback

The JavaScript version is more advanced: it asks Gemini which models are
accessible to your API key and tries text-capable agent models in a preferred
order. A `404` or `429` causes it to try the next model; transient server
errors are retried with exponential backoff.

You may see messages such as:

```text
Model gemini-3.8-flash failed; trying the next available model.
```

This normally means the model is temporarily unavailable or its quota is
exhausted. It is not a failure of your local file tools.

## Safety and limits

- Paths are resolved within the current codebase root.
- The agent can only list, read, and search files; it cannot edit or run code.
- `node_modules`, `.git`, and common build directories are skipped during search.
- Each answer is limited to five tool turns.

## Troubleshooting

**`Set GEMINI_API_KEY ...`** — set one of the API-key variables shown above.

**`Could not list Gemini models` or `fetch failed`** — check your network,
DNS, and API-key access.

**`No available Gemini model could complete the request`** — wait for quota to
reset, check the Gemini API status, or use a key/project with access to one of
the supported text models.

**`Function call is missing a thought_signature`** — upgrade to this version of
the script. It preserves the original Gemini response parts, including the
required thought signature, before sending tool results back.
