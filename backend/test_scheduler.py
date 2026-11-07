from datetime import date, timedelta
import scheduler as S

TOPICS = [{"name": "Organic Chemistry", "level": 5, "details": "SN1 vs SN2"},
          {"name": "Thermodynamics", "level": 4}, {"name": "Calculus", "level": 3}, {"name": "History", "level": 1}]


def test_hard_topics_get_more_time_and_last_day_is_review():
    today = date(2026, 11, 7)
    p = S.build_plan(TOPICS, today + timedelta(days=3), 5, today)
    assert len(p["days"]) == 3 and p["days"][-1]["final"]
    assert p["targets"]["Organic Chemistry"] > p["targets"]["Thermodynamics"] > p["targets"]["Calculus"] > p["targets"]["History"]
    assert all(sum(b["minutes"] for b in d["blocks"]) <= 5 * 60 + 5 * len(TOPICS) for d in p["days"])


def test_replan_boosts_missed_and_keeps_past():
    today = date(2026, 11, 7)
    p = S.build_plan(TOPICS, today + timedelta(days=4), 5, today)
    S.mark_day_progress(p, 1, 0.5)
    S.replan(p, today + timedelta(days=1))
    assert p["days"][0]["date"] == today.isoformat()
    assert any("boosted" in c for c in p["last_changes"])
    assert len(p["days"]) == 4


def test_exam_today_single_session():
    today = date(2026, 11, 7)
    p = S.build_plan(TOPICS, today, 4, today)
    assert len(p["days"]) == 1 and not p["days"][0]["final"]
