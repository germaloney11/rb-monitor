import requests
import json
import os
import hashlib
import re
from datetime import datetime, timezone

# ========== CONFIG ==========
PAGE_URL = "https://www.facebook.com/redbooksire"
NTFY_TOPIC = "redbooks-bookdrop-x7k9m2p"
STATE_FILE = "last_seen.json"
KEYWORD = "BOOK DROP"
# ============================

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
}

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {"seen_hashes": []}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def send_notification(title, message):
    headers = {
        "Title": title,
        "Priority": "high",
        "Tags": "books,loudspeaker"
    }
    requests.post(
        f"https://ntfy.sh/{NTFY_TOPIC}",
        data=message.encode("utf-8"),
        headers=headers
    )
    print(f"Notification sent: {title}")

def main():
    print(f"Checking at {datetime.now(timezone.utc).isoformat()}")

    try:
        response = requests.get(PAGE_URL, headers=HEADERS, timeout=30)
        response.raise_for_status()
        html = response.text
    except Exception as e:
        print(f"Failed to fetch page: {e}")
        return

    # Look for the keyword anywhere in the page
    if KEYWORD.upper() not in html.upper():
        print("No 'BOOK DROP' found on the page")
        return

    # Create a simple hash of the relevant part of the page to avoid re-notifying
    # We take a chunk around the keyword to detect new posts
    matches = list(re.finditer(re.escape(KEYWORD), html, re.IGNORECASE))
    if not matches:
        print("Keyword found but no usable match")
        return

    # Take text around the first few matches
    snippets = []
    for m in matches[:3]:
        start = max(0, m.start() - 200)
        end = min(len(html), m.end() + 400)
        snippets.append(html[start:end])

    content_to_hash = "|||".join(snippets)
    content_hash = hashlib.sha256(content_to_hash.encode("utf-8")).hexdigest()

    state = load_state()
    if content_hash in state.get("seen_hashes", []):
        print("Already notified about this content")
        return

    # New match found
