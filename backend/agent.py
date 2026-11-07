"""Groq tool-calling agent. One conversation history per chat_id (Telegram chat, Switch room, web)."""
import json
from datetime import date

from llm import client, MODEL
from tools import TOOLS, run_tool

HISTORY: dict[str, list] = {}

SYSTEM = """You are Panic Planner, a calm study coach for students who are short on time.
Today is {today}.
Goal: help the room build a day-by-day cram schedule that gives hard topics more time.
Collect: exam date, study hours per day, and each topic with a difficulty (easy=1, okay=2, tricky=3, hard=4, nightmare=5)
and, if they offer it, what they are shaky on. Ask only for what is missing, in one short message.
Rules:
- NEVER calculate minutes yourself. Call build_schedule, then reply with its plan_text exactly as given, then one encouraging line.
- If someone says they fell behind or finished part of a day, call report_progress, then show the new plan_text and explain what changed in one or two sentences.
- If asked for practice questions, call make_quiz.
- Several people may talk in one room. Messages look like "Name: text". Combine everyone's topics into one plan unless told otherwise.
- Keep replies short and chat-friendly."""


def _trim(msgs: list) -> None:
    if len(msgs) > 40:
        del msgs[:-40]
        while msgs and msgs[0]["role"] != "user":
            msgs.pop(0)


def run_agent(chat_id: str, text: str) -> str:
    msgs = HISTORY.setdefault(chat_id, [])
    msgs.append({"role": "user", "content": text})
    _trim(msgs)
    system = {"role": "system", "content": SYSTEM.format(today=date.today().isoformat())}
    for _ in range(6):
        resp = client().chat.completions.create(
            model=MODEL, messages=[system] + msgs, tools=TOOLS, tool_choice="auto", temperature=0.3)
        m = resp.choices[0].message
        if m.tool_calls:
            msgs.append({"role": "assistant", "content": m.content or "", "tool_calls": [
                {"id": tc.id, "type": "function",
                 "function": {"name": tc.function.name, "arguments": tc.function.arguments or "{}"}}
                for tc in m.tool_calls]})
            for tc in m.tool_calls:
                try:
                    args = json.loads(tc.function.arguments or "{}")
                except json.JSONDecodeError:
                    args = {}
                msgs.append({"role": "tool", "tool_call_id": tc.id, "content": run_tool(tc.function.name, args, chat_id)})
            continue
        reply = m.content or ""
        msgs.append({"role": "assistant", "content": reply})
        return reply
    return "Sorry, I got stuck. Please try again."
