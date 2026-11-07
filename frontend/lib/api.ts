export const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export type Block = { id: string; topic: string; level: number; details: string; minutes: number; kind: string; status: "pending" | "done" | "missed" };
export type Day = { date: string; final: boolean; blocks: Block[] };
export type Plan = { id: string; exam_date: string; hours_per_day: number; days: Day[]; last_changes: string[] };

export const LEVELS = ["", "Easy", "Okay", "Tricky", "Hard", "Nightmare"];
export const TIPS = ["", "Skim your notes, then quiz yourself once.", "Read a summary and do a few practice questions.",
  "Work through examples, then redo the ones you missed.", "Do practice problems first, then explain it out loud without notes.",
  "Break it into small parts. Learn, practise, re-test, repeat."];

export const fmt = (m: number) => (m < 60 ? `${m}m` : m % 60 ? `${Math.floor(m / 60)}h ${m % 60}m` : `${m / 60}h`);

export async function call<T>(path: string, body?: unknown): Promise<T> {
  const r = await fetch(API + path, body === undefined ? undefined : {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  if (!r.ok) throw new Error((await r.json().catch(() => ({}))).detail || `Request failed (${r.status})`);
  return r.json();
}
