"""Tools the Groq agent can call. All scheduling math happens in scheduler.py."""
import json
import os
from datetime import date

import scheduler as S
import store
from llm import client, MODEL

FRONTEND = os.getenv("FRONTEND_URL", "http://localhost:3000")
LAST_PLAN: dict[str, str] = {}  # chat_id -> plan_id

TOOLS = [
    {"type": "function", "function": {
        "name": "build_schedule",
        "description": "Build a day-by-day cram schedule. Call once you know the exam date, hours per day and topics.",
        "parameters": {"type": "object", "properties": {
            "exam_date": {"type": "string", "description": "YYYY-MM-DD"},
            "hours_per_day": {"type": "number"},
            "topics": {"type": "array", "items": {"type": "object", "properties": {
                "name": {"type": "string"},
                "level": {"type": "integer", "description": "1 easy, 2 okay, 3 tricky, 4 hard, 5 nightmare"},
                "details": {"type": "string", "description": "what is in it / what the student is shaky on"}},
                "required": ["name", "level"]}}},
            "required": ["exam_date", "hours_per_day", "topics"]}}},
    {"type": "function", "function": {
        "name": "report_progress",
        "description": "Use when the student says they fell behind or finished part of a day. Marks progress and replans.",
        "parameters": {"type": "object", "properties": {
            "day": {"type": "integer", "description": "1-based day number"},
            "fraction_done": {"type": "number", "description": "0 to 1, share of that day finished"},
            "plan_id": {"type": "string", "description": "optional, defaults to this chat's latest plan"}},
            "required": ["day", "fraction_done"]}}},
    {"type": "function", "function": {
        "name": "make_quiz",
        "description": "Make 5 short quiz questions for a topic.",
        "parameters": {"type": "object", "properties": {
            "topic": {"type": "string"}, "details": {"type": "string"}}, "required": ["topic"]}}},
]


def _link(pid: str) -> str:
    return f"{FRONTEND}/plan/{pid}"


def run_tool(name: str, args: dict, chat_id: str) -> str:
    try:
        if name == "build_schedule":
            plan = S.build_plan(args["topics"], date.fromisoformat(args["exam_date"]), float(args["hours_per_day"]))
            store.save_plan(plan)
            LAST_PLAN[chat_id] = plan["id"]
            return json.dumps({"plan_id": plan["id"], "plan_text": S.plan_text(plan, _link(plan["id"]))})
        if name == "report_progress":
            pid = args.get("plan_id") or LAST_PLAN.get(chat_id)
            plan = store.get_plan(pid) if pid else None
            if not plan:
                return json.dumps({"error": "No plan found. Build a schedule first."})
            S.mark_day_progress(plan, int(args["day"]), float(args["fraction_done"]))
            S.replan(plan)
            store.save_plan(plan)
            return json.dumps({"plan_id": plan["id"], "plan_text": S.plan_text(plan, _link(plan["id"]))})
        if name == "make_quiz":
            r = client().chat.completions.create(model=MODEL, temperature=0.4, messages=[
                {"role": "user", "content": f"Write 5 short exam-style quiz questions with answers on: {args['topic']}. "
                                            f"Student is shaky on: {args.get('details', 'n/a')}. Keep it brief."}])
            return r.choices[0].message.content or ""
        return json.dumps({"error": f"Unknown tool {name}"})
    except Exception as e:  # return errors to the model so it can explain them
        return json.dumps({"error": str(e)})
