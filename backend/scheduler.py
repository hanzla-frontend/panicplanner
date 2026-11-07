"""Pure-Python scheduling logic. The LLM never does time math; it calls these functions."""
from __future__ import annotations
import uuid
from datetime import date, timedelta

LEVELS = {1: "Easy", 2: "Okay", 3: "Tricky", 4: "Hard", 5: "Nightmare"}
TIPS = {
    1: "Skim your notes, then quiz yourself once.",
    2: "Read a summary and do a few practice questions.",
    3: "Work through examples, then redo the ones you missed.",
    4: "Do practice problems first, then explain it out loud without notes.",
    5: "Break it into small parts. Learn, practise, re-test, repeat.",
}


def weight(level: int) -> float:
    return level ** 1.8  # harder topics get disproportionately more time


def r5(n: float) -> int:
    return max(5, int(round(n / 5)) * 5)


def days_until(exam: date, today: date | None = None) -> int:
    return (exam - (today or date.today())).days


def _block(topic: dict, minutes: int, kind: str, status: str = "pending") -> dict:
    return {
        "id": uuid.uuid4().hex[:8], "topic": topic["name"], "level": topic["level"],
        "details": topic.get("details", ""), "minutes": minutes, "kind": kind, "status": status,
    }


def _merge(blocks: list[dict]) -> list[dict]:
    out: list[dict] = []
    for b in blocks:
        f = next((x for x in out if x["topic"] == b["topic"] and x["kind"] == b["kind"] and x["status"] == b["status"]), None)
        if f:
            f["minutes"] += b["minutes"]
        else:
            out.append(dict(b))
    return out


def _fill(topics, targets, dates, cap, preset=None):
    preset = preset or {}
    by_name = {t["name"]: t for t in topics}
    order = sorted(targets.items(), key=lambda kv: -by_name[kv[0]]["level"])
    queue = [{"t": by_name[n], "left": m, "started": False} for n, m in order if m > 0]
    out = []
    for d in dates:
        blocks = list(preset.get(d, []))
        room = cap - sum(b["minutes"] for b in blocks)
        while room > 0 and queue:
            it = queue[0]
            chunk = 100 if it["t"]["level"] >= 4 else 75
            m = min(it["left"], room, chunk)
            blocks.append(_block(it["t"], m, "Practice" if it["started"] else "Learn"))
            it["started"] = True
            it["left"] -= m
            room -= m
            if it["left"] <= 0:
                queue.pop(0)
        out.append({"date": d, "blocks": blocks, "final": False})
    if queue and out:  # rounding leftovers go on the last study day
        for it in queue:
            out[-1]["blocks"].append(_block(it["t"], it["left"], "Practice"))
    for day in out:
        day["blocks"] = _merge(day["blocks"])
    return out


def _review_day(topics, d, cap):
    sw = sum(weight(t["level"]) for t in topics)
    blocks = [_block(t, r5(cap * weight(t["level"]) / sw), "Final review")
              for t in sorted(topics, key=lambda t: -t["level"])]
    return {"date": d, "blocks": blocks, "final": True}


def build_plan(topics: list[dict], exam_date: date, hours: float, today: date | None = None) -> dict:
    today = today or date.today()
    topics = [{"name": t["name"].strip(), "level": max(1, min(5, int(t.get("level", 3)))), "details": t.get("details", "")}
              for t in topics if t.get("name", "").strip()]
    if not topics:
        raise ValueError("Add at least one topic.")
    cap = int(round(hours * 60))
    n = max(1, min(30, days_until(exam_date, today)))
    dates = [(today + timedelta(days=i)).isoformat() for i in range(n)]
    study = dates[:-1] if n > 1 else dates
    sw = sum(weight(t["level"]) for t in topics)
    targets = {t["name"]: max(15, r5(cap * len(study) * weight(t["level"]) / sw)) for t in topics}
    days = _fill(topics, targets, study, cap)
    if n > 1:
        days.append(_review_day(topics, dates[-1], cap))
    return {"id": uuid.uuid4().hex[:8], "exam_date": exam_date.isoformat(), "hours_per_day": hours,
            "topics": topics, "targets": targets, "days": days, "last_changes": []}


def replan(plan: dict, today: date | None = None) -> dict:
    """Keep past days and today's finished blocks; respread the remaining work over remaining days."""
    today = today or date.today()
    t_iso = today.isoformat()
    exam = date.fromisoformat(plan["exam_date"])
    cap = int(round(plan["hours_per_day"] * 60))
    topics = plan["topics"]
    done: dict[str, int] = {}
    missed: set[str] = set()
    for d in plan["days"]:
        for b in d["blocks"]:
            if b["kind"] == "Final review":
                continue
            if b["status"] == "done":
                done[b["topic"]] = done.get(b["topic"], 0) + b["minutes"]
            elif b["status"] == "missed":
                missed.add(b["topic"])
    past = [d for d in plan["days"] if d["date"] < t_iso]
    today_done = [b for d in plan["days"] if d["date"] == t_iso for b in d["blocks"]
                  if b["status"] == "done" and b["kind"] != "Final review"]
    n = max(1, min(30, days_until(exam, today)))
    dates = [(today + timedelta(days=i)).isoformat() for i in range(n)]
    study = dates[:-1] if n > 1 else dates
    remaining = {}
    for t in topics:
        r = max(0, plan["targets"][t["name"]] - done.get(t["name"], 0))
        remaining[t["name"]] = r * 1.25 if t["name"] in missed else r
    avail = cap * len(study) - sum(b["minutes"] for b in today_done)
    tot = sum(remaining.values())
    scale = min(1.0, avail / tot) if tot > 0 and avail > 0 else 0.0
    targets = {k: (r5(v * scale) if v * scale >= 5 else 0) for k, v in remaining.items()}
    new_days = _fill(topics, targets, study, cap, {t_iso: today_done} if today_done else None)
    if n > 1:
        new_days.append(_review_day(topics, dates[-1], cap))
    changes = []
    for t in sorted(topics, key=lambda t: -t["level"]):
        k = t["name"]
        note = f"{k}: {targets[k]} min still to study ({done.get(k, 0)} min done)"
        if k in missed:
            note += ", boosted 25% because a block was missed"
        changes.append(note)
    plan["days"] = past + new_days
    plan["last_changes"] = changes
    return plan


def mark_day_progress(plan: dict, day_number: int, fraction_done: float) -> None:
    """Mark the first part of a day as done and the rest as missed (splitting a block if needed)."""
    if not 1 <= day_number <= len(plan["days"]):
        raise ValueError(f"Day must be between 1 and {len(plan['days'])}.")
    day = plan["days"][day_number - 1]
    total = sum(b["minutes"] for b in day["blocks"])
    goal = max(0.0, min(1.0, fraction_done)) * total
    run = 0
    out = []
    for b in day["blocks"]:
        if run + b["minutes"] <= goal:
            b["status"] = "done"
            out.append(b)
        elif run >= goal:
            b["status"] = "missed"
            out.append(b)
        else:  # block straddles the boundary: split it
            part = min(b["minutes"] - 5, max(5, r5(goal - run)))
            if part <= 0 or b["minutes"] <= 5:
                b["status"] = "missed"
                out.append(b)
            else:
                rest = dict(b, id=uuid.uuid4().hex[:8], minutes=b["minutes"] - part, status="missed")
                b["minutes"] = part
                b["status"] = "done"
                out += [b, rest]
        run += b["minutes"] if out[-1] is b else b["minutes"] + out[-1]["minutes"]
    day["blocks"] = out


def fmt(m: int) -> str:
    if m < 60:
        return f"{m}m"
    return f"{m // 60}h {m % 60}m" if m % 60 else f"{m // 60}h"


def plan_text(plan: dict, link: str | None = None) -> str:
    lines = []
    for i, d in enumerate(plan["days"], 1):
        title = f"Day {i} ({d['date']})" + (" - final review" if d["final"] else "")
        lines.append(title)
        for b in d["blocks"]:
            mark = {"done": "[done] ", "missed": "[missed] "}.get(b["status"], "")
            lines.append(f"  - {mark}{b['topic']}: {fmt(b['minutes'])} ({b['kind']})")
    if plan.get("last_changes"):
        lines.append("Changes: " + " | ".join(plan["last_changes"]))
    if link:
        lines.append(f"Full plan: {link}")
    return "\n".join(lines)
