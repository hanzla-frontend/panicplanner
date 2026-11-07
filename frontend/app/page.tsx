"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { call, LEVELS, type Plan } from "../lib/api";

type T = { id: number; name: string; details: string; level: number };
let n = 0;
const blank = (level = 3): T => ({ id: n++, name: "", details: "", level });
const iso = (d: Date) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;

export default function Home() {
  const router = useRouter();
  const d3 = new Date(); d3.setDate(d3.getDate() + 3);
  const [date, setDate] = useState(iso(d3));
  const [hours, setHours] = useState(5);
  const [topics, setTopics] = useState<T[]>([blank(4), blank(3), blank(2)]);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const upd = (id: number, p: Partial<T>) => setTopics((ts) => ts.map((t) => (t.id === id ? { ...t, ...p } : t)));

  async function build() {
    setErr(""); setBusy(true);
    try {
      const plan = await call<Plan>("/plans", {
        exam_date: date, hours_per_day: hours,
        topics: topics.filter((t) => t.name.trim()).map(({ name, level, details }) => ({ name, level, details })),
      });
      router.push(`/plan/${plan.id}`);
    } catch (e) { setErr((e as Error).message); setBusy(false); }
  }

  return (
    <main className="wrap">
      <h1>Panic Planner</h1>
      <p className="hook">“I have 3 days, what do I do?”</p>
      <section className="card row">
        <div><label htmlFor="d">Exam date</label><input id="d" type="date" value={date} min={iso(new Date())} onChange={(e) => setDate(e.target.value)} /></div>
        <div><label htmlFor="h">Study hours per day</label><input id="h" type="number" min={1} max={16} step={0.5} value={hours} onChange={(e) => setHours(+e.target.value || 1)} /></div>
      </section>
      <section className="card">
        {topics.map((t) => (
          <div className="topic" key={t.id}>
            <div className="row end">
              <div><label>Topic name</label><input value={t.name} placeholder="e.g. Thermodynamics" onChange={(e) => upd(t.id, { name: e.target.value })} /></div>
              {topics.length > 1 && <button className="ghost" onClick={() => setTopics((ts) => ts.filter((x) => x.id !== t.id))}>Remove</button>}
            </div>
            <label>How hard is it for you?</label>
            <div className="pills">{[1, 2, 3, 4, 5].map((l) => <button key={l} className={t.level === l ? "on" : ""} onClick={() => upd(t.id, { level: l })}>{LEVELS[l]}</button>)}</div>
            <label>Details (what’s in it, what you’re shaky on)</label>
            <textarea value={t.details} onChange={(e) => upd(t.id, { details: e.target.value })} placeholder="e.g. Entropy problems, I mix up the ΔS formulas" />
          </div>
        ))}
      </section>
      <button className="add" onClick={() => setTopics((ts) => [...ts, blank()])}>Add topic</button>
      <button className="go" disabled={busy} onClick={build}>{busy ? "Building…" : "Build my cram plan"}</button>
      {err && <p className="err">{err}</p>}
    </main>
  );
}
