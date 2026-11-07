# Panic Planner

**"I have 3 days, what do I do?"** An agent that lives in your team chat, asks for your exam date and topics,
and replies with a day-by-day cram schedule that gives hard topics more time. When someone falls behind,
it replans the remaining days.

- **Agent:** custom tool-calling agent on the **Groq API** (default model `llama-3.3-70b-versatile`)
- **Chat platform:** Telegram (via Switch, with a built-in Telegram bridge as fallback)
- **Backend:** FastAPI (scheduler, replanner, agent, plan storage)
- **Frontend:** Next.js (visual plan with Done/Missed checkboxes, plus a web chat for testing)

## How it works

```
Telegram group ──► Switch ──► POST /agent/message (FastAPI) ──► Groq agent
                                                                  ├─ build_schedule  (Python)
                                                                  ├─ report_progress (Python replan)
                                                                  └─ make_quiz       (Groq)
Next.js ──► GET/POST /plans/... (same plans, visual view with a shareable link)
```

The LLM decides what to do and talks to people. **Python does all the time math** (`backend/scheduler.py`),
so the numbers are always consistent: topic time grows with difficulty (level^1.8), hard topics go first in
longer blocks, and the last day is review only.

## Run it

### 1. Backend
```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # add your GROQ_API_KEY (never commit .env)
uvicorn main:app --reload --port 8000
```
Run tests: `pytest` (install with `pip install pytest`).

### 2. Frontend
```bash
cd frontend
cp .env.local.example .env.local
npm install
npm run dev                 # http://localhost:3000
```
Open `/chat` to talk to the agent in the browser, or use the form on the home page.

### 3. Team chat (Switch + Telegram)
1. Create a bot with **@BotFather** on Telegram and copy the token. In BotFather run `/setprivacy` and choose
   **Disable** so the bot can read group messages. Add the bot and your teammates to a group.
2. Connect the agent through **Switch**. Switch's Agent Protocol details are in its docs: set the agent's
   message endpoint to `POST http://<your-backend>/agent/message`
   with JSON `{ "chat_id": "<room id>", "text": "<message>", "user": "<sender name>" }`; it returns `{ "reply": "..." }`.
   Adapt the field names in `main.py` to whatever the protocol sends if they differ.
   Tip: `claude mcp add switch-docs --transport http https://docs.flintai.dev/mcp` lets Claude Code answer setup questions.
3. **Fallback without Switch** (to test the chat flow): put `TELEGRAM_BOT_TOKEN` in `backend/.env` and run
   `python telegram_bot.py`.

## Demo script (under 3 minutes)
1. In the Telegram group, a teammate types: "I have 3 days, what do I do?"
2. The agent asks for exam date, hours per day and topics with difficulty. Two teammates add their topics.
3. The agent posts the day-by-day plan and a link; open the link to show the visual version.
4. A teammate says "I only finished half of Day 1." The agent replans and explains what changed.

## Project layout
```
backend/   main.py  agent.py  tools.py  scheduler.py  store.py  llm.py  telegram_bot.py  test_scheduler.py
frontend/  app/page.tsx  app/plan/[id]/page.tsx  app/chat/page.tsx  lib/api.ts
```
