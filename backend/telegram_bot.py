"""Minimal Telegram bridge (long polling). Use it as a fallback or alongside Switch.
In a group, disable bot privacy in @BotFather (/setprivacy -> Disable) so the bot can read messages."""
import os
import time

import httpx
from dotenv import load_dotenv

load_dotenv()
from agent import run_agent

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
API = f"https://api.telegram.org/bot{TOKEN}"


def main():
    offset = None
    with httpx.Client(timeout=70) as c:
        while True:
            try:
                r = c.get(f"{API}/getUpdates", params={"timeout": 50, "offset": offset}).json()
                for u in r.get("result", []):
                    offset = u["update_id"] + 1
                    msg = u.get("message") or {}
                    text = msg.get("text")
                    if not text:
                        continue
                    chat = msg["chat"]["id"]
                    who = msg.get("from", {}).get("first_name", "")
                    reply = run_agent(f"tg-{chat}", f"{who}: {text}")
                    c.post(f"{API}/sendMessage", json={"chat_id": chat, "text": reply})
            except Exception as e:
                print("error:", e)
                time.sleep(3)


if __name__ == "__main__":
    main()
