import os
from datetime import date
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

load_dotenv(Path(__file__).resolve().with_name(".env"))
import scheduler as S
import store

app = FastAPI(title="Panic Planner API")
app.add_middleware(CORSMiddleware, allow_origins=[os.getenv("FRONTEND_URL", "http://localhost:3000")],
                   allow_methods=["*"], allow_headers=["*"])


class TopicIn(BaseModel):
    name: str
    level: int = Field(3, ge=1, le=5)
    details: str = ""


class PlanIn(BaseModel):
    exam_date: date
    hours_per_day: float = Field(5, gt=0, le=16)
    topics: list[TopicIn]


class ProgressIn(BaseModel):
    block_id: str
    status: str = Field(pattern="^(pending|done|missed)$")


class MessageIn(BaseModel):
    chat_id: str
    text: str
    user: str | None = None


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/plans")
def create_plan(body: PlanIn):
    try:
        plan = S.build_plan([t.model_dump() for t in body.topics], body.exam_date, body.hours_per_day)
    except ValueError as e:
        raise HTTPException(400, str(e))
    store.save_plan(plan)
    return plan


@app.get("/plans/{plan_id}")
def read_plan(plan_id: str):
    plan = store.get_plan(plan_id)
    if not plan:
        raise HTTPException(404, "Plan not found")
    return plan


@app.post("/plans/{plan_id}/progress")
def set_progress(plan_id: str, body: ProgressIn):
    plan = store.get_plan(plan_id)
    if not plan:
        raise HTTPException(404, "Plan not found")
    for d in plan["days"]:
        for b in d["blocks"]:
            if b["id"] == body.block_id:
                b["status"] = body.status
                store.save_plan(plan)
                return plan
    raise HTTPException(404, "Block not found")


@app.post("/plans/{plan_id}/replan")
def do_replan(plan_id: str):
    plan = store.get_plan(plan_id)
    if not plan:
        raise HTTPException(404, "Plan not found")
    S.replan(plan)
    store.save_plan(plan)
    return plan


@app.post("/agent/message")
def agent_message(body: MessageIn):
    """Generic chat entry point. Point Switch (or any chat bridge) at this endpoint."""
    from agent import run_agent
    text = f"{body.user}: {body.text}" if body.user else body.text
    try:
        return {"reply": run_agent(body.chat_id, text)}
    except Exception as e:
        raise HTTPException(500, str(e))
