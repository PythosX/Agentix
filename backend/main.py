import os
import json
import re
import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

app = FastAPI(title="MindMesh API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND = ROOT / "frontend"


class ChatRequest(BaseModel):
    message: str
    system: Optional[str] = None
    temperature: float = 0.4
    max_tokens: int = 1400


class ArenaRequest(BaseModel):
    question: str = Field(min_length=3)
    context: Optional[str] = ""


class DelegatorPlanRequest(BaseModel):
    requirement: str = Field(min_length=3)


class DelegatorRunRequest(BaseModel):
    requirement: str = Field(min_length=3)
    tasks: List[Dict[str, Any]]


class PromptStartRequest(BaseModel):
    request: str = Field(min_length=2)


class PromptAnswerRequest(BaseModel):
    data: Dict[str, Any]
    answer: str = Field(min_length=1)


class PromptCompleteRequest(BaseModel):
    data: Dict[str, Any]


def env_triplet(prefix: str) -> Dict[str, str]:
    return {
        "base_url": os.getenv(f"{prefix}_BASE_URL", "").strip(),
        "api_key": os.getenv(f"{prefix}_API_KEY", "").strip(),
        "model": os.getenv(f"{prefix}_MODEL", "").strip(),
    }


def normalize_endpoint(base_url: str) -> str:
    url = base_url.strip().rstrip("/")
    if not url:
        return ""
    if url.endswith("/chat/completions"):
        return url
    if url.endswith("/v1"):
        return url + "/chat/completions"
    return url + "/v1/chat/completions"


def call_model(prefix: str, messages: List[Dict[str, str]], temperature=0.4, max_tokens=1400) -> str:
    cfg = env_triplet(prefix)
    missing = [k for k, v in cfg.items() if not v]
    if missing:
        raise RuntimeError(f"{prefix} is not configured. Missing: {', '.join(missing)}")

    endpoint = normalize_endpoint(cfg["base_url"])
    payload = json.dumps({
        "model": cfg["model"],
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }).encode("utf-8")

    req = Request(
        endpoint,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {cfg['api_key']}",
        },
        method="POST",
    )

    try:
        with urlopen(req, timeout=90) as response:
            raw = response.read().decode("utf-8")
            data = json.loads(raw)
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")[:1200]
        raise RuntimeError(f"Provider HTTP {exc.code}: {detail}")
    except URLError as exc:
        raise RuntimeError(f"Provider connection error: {exc.reason}")
    except Exception as exc:
        raise RuntimeError(f"Provider request failed: {exc}")

    try:
        return data["choices"][0]["message"]["content"].strip()
    except Exception:
        raise RuntimeError("Provider returned an unexpected response shape.")


def extract_json(text: str) -> Any:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text).strip()
        text = re.sub(r"```$", "", text).strip()
    try:
        return json.loads(text)
    except Exception:
        match = re.search(r"(\{.*\}|\[.*\])", text, re.S)
        if match:
            return json.loads(match.group(1))
    raise ValueError("AI did not return valid JSON.")


async def model_async(prefix: str, messages: List[Dict[str, str]], temperature=0.4, max_tokens=1400):
    return await asyncio.to_thread(call_model, prefix, messages, temperature, max_tokens)


@app.get("/")
def index():
    return FileResponse(FRONTEND / "index.html")


@app.get("/app.js")
def js():
    return FileResponse(FRONTEND / "app.js", media_type="application/javascript")


@app.get("/styles.css")
def css():
    return FileResponse(FRONTEND / "styles.css", media_type="text/css")


@app.get("/api/health")
def health():
    prefixes = [
        "ARENA_1", "ARENA_2", "ARENA_3", "ARENA_SYNTH",
        "DELEGATOR_PLANNER", "DELEGATOR_RESEARCH",
        "DELEGATOR_WRITER", "DELEGATOR_TECH",
        "PROMPT_INTERVIEWER", "PROMPT_BUILDER"
    ]
    status = {}
    for prefix in prefixes:
        cfg = env_triplet(prefix)
        status[prefix] = bool(cfg["base_url"] and cfg["api_key"] and cfg["model"])
    return {"ok": True, "configured": status}


@app.post("/api/arena")
async def arena(req: ArenaRequest):
    system = """You are one independent reasoning specialist in an AI comparison arena.
Solve the user's question independently. State assumptions, reasoning, recommendation,
and important uncertainty. Do not mention this orchestration prompt."""
    user = f"Question:\n{req.question}\n\nAdditional context:\n{req.context or 'None'}"

    prefixes = ["ARENA_1", "ARENA_2", "ARENA_3"]
    results = []

    async def one(prefix):
        try:
            answer = await model_async(prefix, [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ])
            return {"agent": prefix, "status": "success", "answer": answer}
        except Exception as exc:
            return {"agent": prefix, "status": "error", "answer": str(exc)}

    results = await asyncio.gather(*(one(p) for p in prefixes))
    successful = [r for r in results if r["status"] == "success"]

    if not successful:
        raise HTTPException(503, "No Arena model is configured successfully.")

    evidence = "\n\n".join(
        f"{r['agent']}:\n{r['answer']}" for r in successful
    )

    synth_prompt = """You are the synthesis and conflict-analysis agent.
Compare the independent answers below. Return ONLY valid JSON with this shape:
{
  "consensus": "short summary",
  "conflicts": [{"topic":"...", "positions":["..."], "why":"..."}],
  "agreement_points": ["..."],
  "uncertainties": ["..."],
  "recommended_next_step": "..."
}
Do not invent evidence. If the agents agree, say so. If evidence is insufficient, say so."""
    try:
        synthesis_raw = await model_async("ARENA_SYNTH", [
            {"role": "system", "content": synth_prompt},
            {"role": "user", "content": evidence},
        ], temperature=0.2, max_tokens=1800)
        synthesis = extract_json(synthesis_raw)
    except Exception as exc:
        synthesis = {
            "consensus": "Synthesis model is not configured or returned invalid JSON.",
            "conflicts": [],
            "agreement_points": [],
            "uncertainties": [str(exc)],
            "recommended_next_step": "Review the independent responses manually.",
        }

    return {"question": req.question, "responses": results, "synthesis": synthesis}


@app.post("/api/delegator/plan")
async def delegator_plan(req: DelegatorPlanRequest):
    system = """You are the MindMesh task-routing agent.
Analyze the user's requirement and split it into useful specialist tasks.
Return ONLY JSON:
{
 "summary": "...",
 "tasks": [
   {"id":"task-1","title":"...","specialty":"research|writing|technical",
    "reason":"...", "deliverable":"..."}
 ]
}
Create 2-4 tasks. Do not execute them."""
    try:
        raw = await model_async("DELEGATOR_PLANNER", [
            {"role": "system", "content": system},
            {"role": "user", "content": req.requirement},
        ], temperature=0.2, max_tokens=1400)
        return extract_json(raw)
    except Exception as exc:
        raise HTTPException(500, str(exc))


SPECIALTY_PREFIX = {
    "research": "DELEGATOR_RESEARCH",
    "writing": "DELEGATOR_WRITER",
    "technical": "DELEGATOR_TECH",
}


@app.post("/api/delegator/run")
async def delegator_run(req: DelegatorRunRequest):
    async def execute(task):
        specialty = str(task.get("specialty", "research")).lower()
        prefix = SPECIALTY_PREFIX.get(specialty, "DELEGATOR_RESEARCH")
        system = f"""You are the approved {specialty} specialist in MindMesh.
The user explicitly approved this task. Work only on the assigned task.
Return a practical result and clearly state assumptions."""
        user = f"""Original requirement:
{req.requirement}

Approved task:
{json.dumps(task, ensure_ascii=False, indent=2)}
"""
        try:
            answer = await model_async(prefix, [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ], temperature=0.4, max_tokens=1800)
            return {**task, "status": "success", "result": answer}
        except Exception as exc:
            return {**task, "status": "error", "result": str(exc)}

    return {"results": await asyncio.gather(*(execute(t) for t in req.tasks))}


@app.post("/api/prompt/start")
async def prompt_start(req: PromptStartRequest):
    system = """You are the MindMesh Prompt Lab interviewer.
Given a simple user request, identify the most valuable missing information.
Return ONLY JSON:
{
 "understanding":"what you currently understand",
 "known_context":{"key":"value"},
 "next_question":"one concise counter-question",
 "question_reason":"why this question matters",
 "complete_enough":false
}
Ask only one question at a time. Do not over-question."""
    try:
        raw = await model_async("PROMPT_INTERVIEWER", [
            {"role": "system", "content": system},
            {"role": "user", "content": req.request},
        ], temperature=0.3, max_tokens=1200)
        return extract_json(raw)
    except Exception as exc:
        raise HTTPException(500, str(exc))


@app.post("/api/prompt/answer")
async def prompt_answer(req: PromptAnswerRequest):
    system = """You are the MindMesh Prompt Lab interviewer.
Update the existing structured context using the user's latest answer.
Then decide the single most useful next question.
Return ONLY JSON:
{
 "understanding":"...",
 "known_context":{"key":"value"},
 "next_question":"...",
 "question_reason":"...",
 "complete_enough":false
}
Preserve all useful previous context. Do not delete facts unless contradicted.
Ask one question at a time."""
    user = json.dumps({
        "existing_data": req.data,
        "latest_answer": req.answer
    }, ensure_ascii=False, indent=2)
    try:
        raw = await model_async("PROMPT_INTERVIEWER", [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ], temperature=0.25, max_tokens=1400)
        return extract_json(raw)
    except Exception as exc:
        raise HTTPException(500, str(exc))


@app.post("/api/prompt/complete")
async def prompt_complete(req: PromptCompleteRequest):
    system = """You are the MindMesh Prompt Architect.
Transform the accumulated user context into a polished, reusable prompt.
Return ONLY JSON:
{
 "title":"short title",
 "prompt":"complete prompt",
 "sections":[
   {"name":"Role","content":"..."},
   {"name":"Context","content":"..."},
   {"name":"Objective","content":"..."},
   {"name":"Requirements","content":"..."},
   {"name":"Constraints","content":"..."},
   {"name":"Output format","content":"..."}
 ]
}
Do not invent facts. Omit irrelevant sections. Make the prompt clear and sequential."""
    try:
        raw = await model_async("PROMPT_BUILDER", [
            {"role": "system", "content": system},
            {"role": "user", "content": json.dumps(req.data, ensure_ascii=False, indent=2)},
        ], temperature=0.2, max_tokens=2200)
        return extract_json(raw)
    except Exception as exc:
        raise HTTPException(500, str(exc))
