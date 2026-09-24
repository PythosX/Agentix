# MindMesh — Step-by-step hackathon setup

## Step 1 — Download and extract

Extract the ZIP. You should see:

- backend
- frontend
- docs
- `.env.example`
- `README.md`

## Step 2 — Install Python

Use a current Python 3.x installation.

Check:

```bash
python --version
```

## Step 3 — Create a virtual environment

Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

macOS/Linux:

```bash
python -m venv .venv
source .venv/bin/activate
```

## Step 4 — Install dependencies

```bash
pip install -r backend/requirements.txt
```

## Step 5 — Create your environment file

Make a copy of:

```text
.env.example
```

and rename the copy to:

```text
.env
```

Do NOT rename the variable names.

## Step 6 — Add API keys and model identifiers

The only place you should put secrets/model identifiers is `.env`.

### AI Arena

```text
ARENA_1_BASE_URL=your_provider_base_url
ARENA_1_API_KEY=your_key
ARENA_1_MODEL=your_model_identifier

ARENA_2_BASE_URL=your_provider_base_url
ARENA_2_API_KEY=your_key
ARENA_2_MODEL=your_model_identifier

ARENA_3_BASE_URL=your_provider_base_url
ARENA_3_API_KEY=your_key
ARENA_3_MODEL=your_model_identifier

ARENA_SYNTH_BASE_URL=your_provider_base_url
ARENA_SYNTH_API_KEY=your_key
ARENA_SYNTH_MODEL=your_model_identifier
```

Use different providers/models for Arena when possible. The code does not contain a specific model name.

### AI Delegator

Planner:

```text
DELEGATOR_PLANNER_BASE_URL=
DELEGATOR_PLANNER_API_KEY=
DELEGATOR_PLANNER_MODEL=
```

Research specialist:

```text
DELEGATOR_RESEARCH_BASE_URL=
DELEGATOR_RESEARCH_API_KEY=
DELEGATOR_RESEARCH_MODEL=
```

Writing specialist:

```text
DELEGATOR_WRITER_BASE_URL=
DELEGATOR_WRITER_API_KEY=
DELEGATOR_WRITER_MODEL=
```

Technical specialist:

```text
DELEGATOR_TECH_BASE_URL=
DELEGATOR_TECH_API_KEY=
DELEGATOR_TECH_MODEL=
```

### Prompt Lab

Interviewer:

```text
PROMPT_INTERVIEWER_BASE_URL=
PROMPT_INTERVIEWER_API_KEY=
PROMPT_INTERVIEWER_MODEL=
```

Prompt architect:

```text
PROMPT_BUILDER_BASE_URL=
PROMPT_BUILDER_API_KEY=
PROMPT_BUILDER_MODEL=
```

## Step 7 — Where to get provider values

For every provider you choose, locate these three pieces in that provider's developer console:

1. API key
2. Base URL / API endpoint
3. Model identifier

Put them into the corresponding `.env` variables.

This project intentionally does not decide your provider or model. That keeps the code portable and prevents a model name from being embedded in the project.

## Step 8 — Important endpoint format

The backend expects an OpenAI-compatible chat-completions API.

If your provider documents an endpoint similar to:

```text
https://provider.example/v1/chat/completions
```

put the provider's documented base URL into `*_BASE_URL`.

The backend automatically handles common forms ending in `/v1` or `/chat/completions`.

## Step 9 — Run locally

```bash
uvicorn backend.main:app --reload
```

Open:

```text
http://127.0.0.1:8000
```

## Step 10 — Check configuration

Click:

**System status**

The app shows how many AI slots are configured.

If Arena has 4 configured slots, it will report them. If a slot is missing, the error will tell you which variable is missing.

## Step 11 — Test Arena

Use a question where different models may reasonably have different opinions.

Example:

```text
What architecture should I use for a free AI startup MVP with a Python backend?
```

You should see:

- independent responses
- status per model
- consensus
- conflicts
- uncertainties
- recommended next step

## Step 12 — Test Delegator

Use:

```text
I want to launch an AI learning platform for college students and need a research plan, content strategy and technical architecture.
```

The planner should return 2–4 tasks.

Select only the tasks you want.

Click:

**Run Approved Agents**

Only selected tasks are executed.

## Step 13 — Test Prompt Lab

Start with:

```text
Create a website for my clothing business.
```

Answer the counter-questions.

Watch the context map grow.

When ready, click:

**Complete Prompt**

Then copy the final prompt.

## Step 14 — Deploy

### Render-style Python deployment

Build command:

```text
pip install -r backend/requirements.txt
```

Start command:

```text
uvicorn backend.main:app --host 0.0.0.0 --port $PORT
```

Add the same environment variables from your local `.env` into the hosting platform's environment-variable section.

Do not upload `.env` to GitHub.

### GitHub

```bash
git init
git add .
git commit -m "MindMesh hackathon MVP"
git branch -M main
git remote add origin YOUR_REPOSITORY_URL
git push -u origin main
```

## Step 15 — Hackathon safety checklist

Before recording:

- [ ] `.env` is not in Git
- [ ] all required model slots are configured
- [ ] API quotas are sufficient for the demo
- [ ] Arena returns at least two successful independent responses
- [ ] synthesis works
- [ ] Delegator asks for approval before execution
- [ ] Prompt Lab retains previous answers
- [ ] Complete Prompt works
- [ ] Copy button works
- [ ] mobile layout is usable
- [ ] live deployment works
- [ ] demo uses realistic input


### Optional OpenRouter fallback models

For any slot that may be rate-limited, add a comma-separated fallback list. Example:

`ARENA_2_FALLBACK_MODELS=provider/backup-model-1,provider/backup-model-2`

Keep the primary model ID unchanged. Fallbacks are only used when needed.
