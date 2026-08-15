import requests
import json
import os
import hashlib
import re
from datetime import datetime, timezone

# ========== CONFIG ==========
PAGE_URLS = [
    "https://www.facebook.com/redbooksire",
    "https://mbasic.facebook.com/redbooksire",
    "https://mbasic.facebook.com/redbooksire?v=timeline",
]
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

def fetch_page(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=25)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Failed to fetch {url}: {e}")
        return None

def main():
    print(f"Checking at {datetime.now(timezone.utc).isoformat()}")

    html = None
    used_url = None

    # Try normal page first, then mbasic fallbacks
    for url in PAGE_URLS:
        print(f"Trying {url}")
        html = fetch_page(url)
        if html and KEYWORD.upper() in html.upper():
            used_url = url
            print(f"Found keyword on {url}")
            break
        elif html:
            print(f"Page loaded but no '{KEYWORD}' found")
        else:
            print("Page failed to load")

    if not html or KEYWORD.upper() not in html.upper():
        print("No 'BOOK DROP' found on any URL")
        return

    # Create a hash of text around the keyword to avoid duplicate notifications
    matches = list(re.finditer(re.escape(KEYWORD), html, re.IGNORECASE))
    if not matches:
        print("Keyword found but no usable match positions")
        return

    snippets = []
    for m in matches[:3]:
        start = max(0, m.start() - 250)
        end = min(len(html), m.end() + 450)
        snippets.append(html[start:end])

    content_to_hash = "|||".join(snippets)
    content_hash = hashlib.sha256(content_to_hash.encode("utf-8")).hexdigest()

    state = load_state()
    if content_hash in state.get("seen_hashes", []):
        print("Already notified about this content")
        return

    # New match → send notification
    send_notification(
        title="BOOK DROP at Red Books!",
        message="A new post containing 'BOOK DROP' was detected.\n\nOpen the page:\nhttps://www.facebook.com/redbooksire"
    )

    state.setdefault("seen_hashes", []).append(content_hash)
    state["seen_hashes"] = state["seen_hashes"][-20:]
    save_state(state)
    print("New Book Drop detected and notified")

if __name__ == "__main__":
    main()
