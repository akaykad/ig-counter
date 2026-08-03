#!/usr/bin/env python3
import os
import json
import subprocess
from datetime import datetime, timezone

import requests

USERNAME = "thapletcom"
USER_ID = "47074278351"

REPO_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(REPO_DIR, "followers.json")
HISTORY_FILE = os.path.join(REPO_DIR, "history.json")
MAX_POINTS = 2000

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


def load_sessionid():
    path = os.path.join(REPO_DIR, "session.txt")
    if os.path.exists(path):
        with open(path) as f:
            return f.read().strip()
    return os.environ.get("IG_SESSIONID", "")


def make_session():
    s = requests.Session()
    sid = load_sessionid()
    if sid:
        s.cookies.set("sessionid", sid, domain=".instagram.com")
    s.get("https://www.instagram.com/", headers={"User-Agent": UA}, timeout=20)
    return s


def get_profile(session, user_id):
    r = session.get(
        f"https://i.instagram.com/api/v1/users/{user_id}/info/",
        headers={
            "User-Agent": UA,
            "x-ig-app-id": "936619743392459",
            "x-csrftoken": session.cookies.get("csrftoken", ""),
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
        },
        timeout=20,
    )
    r.raise_for_status()
    return r.json()["user"]


def append_history(count, when):
    history = []
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE) as f:
                history = json.load(f)
        except Exception:
            history = []
    history.append({"t": when, "followers": count})
    history = history[-MAX_POINTS:]
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f)


def publish(user):
    count = user["follower_count"]
    now = datetime.now(timezone.utc).isoformat()

    with open(DATA_FILE, "w") as f:
        json.dump(
            {
                "followers": count,
                "following": user.get("following_count"),
                "posts": user.get("media_count"),
                "username": user.get("username"),
                "full_name": user.get("full_name"),
                "is_verified": user.get("is_verified", False),
                "updated": now,
            },
            f,
        )

    append_history(count, now)

    def git(*args):
        return subprocess.run(["git", "-C", REPO_DIR, *args])

    git("add", "followers.json", "history.json")
    has_change = git("diff", "--cached", "--quiet").returncode != 0
    if has_change:
        git("commit", "-m", f"update: {count} followers")
        git("push")
        print(f"Published {count} followers.")
    else:
        print(f"No change ({count}). Nothing to push.")


if __name__ == "__main__":
    try:
        session = make_session()
        profile = get_profile(session, USER_ID)
        publish(profile)
    except Exception as e:
        print(f"ERROR: {e}")
        raise
