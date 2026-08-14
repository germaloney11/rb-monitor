import feedparser
import json
import os
import requests
from datetime import datetime, timezone

# ========== CONFIG ==========
RSS_URL = "https://fetchrss.com/feed/1wumYkGtDCiB1wumXv9YU4A7.rss"
NTFY_TOPIC = "redbooks-bookdrop-x7k9m2p"
STATE_FILE = "last_seen.json"
KEYWORD = "BOOK DROP"
# ============================

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {"seen": []}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def send_notification(title, message, link=None):
    headers = {
        "Title": title,
        "Priority": "high",
        "Tags": "books,loudspeaker"
    }
    if link:
        headers["Click"] = link
        headers["Actions"] = f"view, Open Post, {link}"

    requests.post(
        f"https://ntfy.sh/{NTFY_TOPIC}",
        data=message.encode("utf-8"),
        headers=headers
    )
    print(f"Notification sent: {title}")

def main():
    print(f"Checking at {datetime.now(timezone.utc).isoformat()}")
    feed = feedparser.parse(RSS_URL)

    if feed.bozo:
        print("Feed parsing issue:", feed.bozo_exception)

    state = load_state()
    new_matches = []

    for entry in feed.entries:
        post_id = entry.get("id") or entry.get("guid") or entry.get("link") or entry.title
        title = entry.get("title", "")
        summary = entry.get("summary", "") or entry.get("description", "")
        link = entry.get("link", "")

        full_text = f"{title} {summary}".upper()

        if KEYWORD.upper() in full_text:
            if post_id not in state.get("seen", []):
                new_matches.append({
                    "id": post_id,
                    "title": title,
                    "link": link,
                    "summary": summary[:400]
                })

    if new_matches:
        for match in reversed(new_matches):
            send_notification(
                title="BOOK DROP at Red Books!",
                message=f"{match['title']}\n\n{match['summary']}",
                link=match["link"]
            )
            state.setdefault("seen", []).append(match["id"])

        state["seen"] = state["seen"][-50:]
        save_state(state)
        print(f"Notified {len(new_matches)} new Book Drop post(s)")
    else:
        print("No new Book Drop posts found")

if __name__ == "__main__":
    main()
