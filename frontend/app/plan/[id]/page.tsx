"use client";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { API, call, fmt, TIPS, type Plan } from "../../../lib/api";

const col = (l: number) => (l >= 4 ? "var(--hard)" : l === 3 ? "var(--mid)" : "var(--easy)");

export default function PlanPage() {
  const { id } = useParams<{ id: string }>();
  const [plan, setPlan] = useState<Plan | null>(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    fetch(`${API}/plans/${id}`).then((r) => (r.ok ? r.json() : Promise.reject(new Error("Plan not found"))))
      .then(setPlan).catch((e) => setErr(e.message));
  }, [id]);

  const mark = async (blockId: string, status: string) => setPlan(await call<Plan>(`/plans/${id}/progress`, { block_id: blockId, status }));
  const replan = async () => setPlan(await call<Plan>(`/plans/${id}/replan`, {}));

  if (err) return <main className="wrap"><p className="err">{err}</p></main>;
  if (!plan) return <main className="wrap"><p className="note">Loading…</p></main>;
  const load = (d: Plan["days"][number]) => d.blocks.reduce((a, b) => a + b.minutes, 0);
  const max = Math.max(...plan.days.map(load), 1);

  return (
    <main className="wrap">
      <h1>Your cram plan</h1>
      <p className="note">Exam {plan.exam_date}. Mark blocks Done or Missed, then replan to shift the remaining time.</p>
      <button className="go" onClick={replan}>Replan from today</button>
      {plan.last_changes.length > 0 && (
        <section className="card"><b>What changed</b>{plan.last_changes.map((c, i) => <div className="bm" key={i}>{c}</div>)}</section>
      )}
      <div className="plan">
        {plan.days.map((d, i) => (
          <section className="card" key={d.date}>
            <h3><span>Day {i + 1}: {new Date(d.date + "T00:00:00").toLocaleDateString(undefined, { weekday: "short", month: "short", day: "numeric" })}</span>
              <span className="tag">{d.final ? "Final review" : fmt(load(d))}</span></h3>
            <div className="bar"><i style={{ width: `${(load(d) / max) * 100}%` }} /></div>
            {d.blocks.map((b) => (
              <div className={`blk ${b.status}`} key={b.id}>
                <span className="dot" style={{ background: col(b.level) }} />
                <div style={{ flex: 1 }}>
                  <div className="bt">{b.topic} <span className="tag">{b.kind}</span></div>
                  <div className="bm">{b.kind === "Final review" ? "Flashcards, formulas and earlier mistakes. No new material." : TIPS[b.level]}</div>
                  {b.details && b.kind !== "Final review" && <div className="bm">Focus: {b.details}</div>}
                  <div className="acts">
                    <button className={b.status === "done" ? "on" : ""} onClick={() => mark(b.id, b.status === "done" ? "pending" : "done")}>Done</button>
                    <button className={b.status === "missed" ? "on miss" : ""} onClick={() => mark(b.id, b.status === "missed" ? "pending" : "missed")}>Missed</button>
                  </div>
                </div>
                <span className="mins">{fmt(b.minutes)}</span>
              </div>
            ))}
          </section>
        ))}
      </div>
    </main>
  );
}
