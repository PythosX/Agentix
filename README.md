# MindMesh — Hackathon Ready MVP

**Many AI minds. One intelligent workflow.**

MindMesh is a multi-agent AI workspace built around three controlled workflows:

1. **AI Arena** — sends the same question to multiple independently configured AI models, compares their outputs, detects conflicts, and asks a synthesis model to produce a structured conclusion.
2. **AI Delegator** — analyzes a complex requirement, breaks it into specialist tasks, asks the user for permission for each task, and executes only approved tasks with separate model configurations.
3. **Prompt Lab** — starts from a simple request, asks targeted counter-questions, accumulates structured context, and generates a clean final prompt when the user clicks Complete Prompt.

## Architecture

```text
Browser
  |
  v
FastAPI backend
  |
  +--> Arena:      ARENA_1 / ARENA_2 / ARENA_3 + ARENA_SYNTH
  |
  +--> Delegator:  DELEGATOR_PLANNER + specialist model slots
  |
  +--> Prompt Lab: PROMPT_INTERVIEWER + PROMPT_BUILDER
  |
  v
OpenAI-compatible chat-completions endpoints
```

**Important:** No provider-specific model names are hard-coded. Put your own model identifiers and API keys in `.env`.

## Free-first design

The app does not require a paid database or paid frontend service. For the hackathon demo, use free API quotas where available, or connect local/open models through an OpenAI-compatible endpoint. Free quotas are provider-specific and can change.

## Quick start

### 1. Create Python environment

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

macOS/Linux:

```bash
source .venv/bin/activate
```

### 2. Install

```bash
pip install -r backend/requirements.txt
```

### 3. Configure

Copy:

```text
.env.example -> .env
```

Then fill in the API keys, base URLs, and model identifiers.

### 4. Run

```bash
uvicorn backend.main:app --reload
```

Open:

```text
http://127.0.0.1:8000
```

## Environment variables

### Arena

```text
ARENA_1_BASE_URL=
ARENA_1_API_KEY=
ARENA_1_MODEL=

ARENA_2_BASE_URL=
ARENA_2_API_KEY=
ARENA_2_MODEL=

ARENA_3_BASE_URL=
ARENA_3_API_KEY=
ARENA_3_MODEL=

ARENA_SYNTH_BASE_URL=
ARENA_SYNTH_API_KEY=
ARENA_SYNTH_MODEL=
```

### Delegator

```text
DELEGATOR_PLANNER_BASE_URL=
DELEGATOR_PLANNER_API_KEY=
DELEGATOR_PLANNER_MODEL=

DELEGATOR_RESEARCH_BASE_URL=
DELEGATOR_RESEARCH_API_KEY=
DELEGATOR_RESEARCH_MODEL=

DELEGATOR_WRITER_BASE_URL=
DELEGATOR_WRITER_API_KEY=
DELEGATOR_WRITER_MODEL=

DELEGATOR_TECH_BASE_URL=
DELEGATOR_TECH_API_KEY=
DELEGATOR_TECH_MODEL=
```

### Prompt Lab

```text
PROMPT_INTERVIEWER_BASE_URL=
PROMPT_INTERVIEWER_API_KEY=
PROMPT_INTERVIEWER_MODEL=

PROMPT_BUILDER_BASE_URL=
PROMPT_BUILDER_API_KEY=
PROMPT_BUILDER_MODEL=
```

All model fields are intentionally blank. The application reads them only from environment variables.

## Provider compatibility

The included adapter expects an OpenAI-compatible endpoint:

```text
POST {BASE_URL}/chat/completions
```

with a JSON body containing `model`, `messages`, `temperature`, and `max_tokens`.

If your provider gives a base URL that already includes `/chat/completions`, set it exactly as provided; the backend normalizes common URL forms.

## Security

- API keys are server-side only.
- `.env` is ignored by git.
- Never put provider keys in frontend JavaScript.
- Do not commit `.env`.

## Hackathon demo flow

1. Open **AI Arena** and submit a question where multiple models can reasonably disagree.
2. Show three model outputs side by side.
3. Show the conflict/consensus summary.
4. Open **AI Delegator**, enter a complex requirement.
5. Review detected specialist tasks and approve only selected tasks.
6. Open **Prompt Lab**, start with a one-line request.
7. Answer counter-questions.
8. Click **Complete Prompt** and copy the structured result.

## Folder structure

```text
MindMesh-Hackathon/
├── backend/
│   ├── main.py
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── app.js
│   └── styles.css
├── docs/
│   └── HACKATHON_SETUP.md
├── .env.example
├── .gitignore
├── Procfile
└── README.md
```


## OpenRouter fallback models

MindMesh supports optional per-agent fallback model IDs. Put comma-separated IDs in the matching `*_FALLBACK_MODELS` environment variable. The primary model remains first; fallback IDs are used when the primary model cannot complete the request.

The UI also shows an animated thinking state while Arena or Delegator models are running.
