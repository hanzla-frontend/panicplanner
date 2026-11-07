"use client";
import { useRef, useState } from "react";
import { call } from "../../lib/api";

type Msg = { role: "me" | "bot"; text: string };

export default function Chat() {
  const room = useRef("web-" + Math.random().toString(36).slice(2, 8));
  const [msgs, setMsgs] = useState<Msg[]>([{ role: "bot", text: "Hi, I’m Panic Planner. Tell me: “I have 3 days, what do I do?”" }]);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);

  async function send() {
    const t = text.trim(); if (!t || busy) return;
    setText(""); setBusy(true); setMsgs((m) => [...m, { role: "me", text: t }]);
    try {
      const r = await call<{ reply: string }>("/agent/message", { chat_id: room.current, text: t });
      setMsgs((m) => [...m, { role: "bot", text: r.reply }]);
    } catch (e) { setMsgs((m) => [...m, { role: "bot", text: "Error: " + (e as Error).message }]); }
    setBusy(false);
  }

  return (
    <main className="wrap">
      <h1>Coach chat</h1>
      <p className="note">Same agent that runs in the team chat. Great for testing without Telegram.</p>
      <div className="chat">{msgs.map((m, i) => <div key={i} className={`msg ${m.role}`}>{m.text}</div>)}{busy && <div className="msg bot">Thinking…</div>}</div>
      <div className="row"><input value={text} onChange={(e) => setText(e.target.value)} onKeyDown={(e) => e.key === "Enter" && send()} placeholder="Type a message" />
        <button className="go" style={{ flex: "none", width: 90 }} onClick={send}>Send</button></div>
    </main>
  );
}
