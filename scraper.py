#!/usr/bin/env python3
"""
Fetches a public Instagram account's follower count and publishes it
to followers.json in this repo, then commits + pushes so GitHub Pages
serves the updated number.

Runs on YOUR device (home PC / Raspberry Pi / phone via Termux) because
Instagram blocks datacenter IPs. Your home internet is a residential IP,
so it works.

Only thing you must edit: USERNAME below.
"""

import os
import json
import subprocess
from datetime import datetime, timezone

import requests

# ---- EDIT THIS -------------------------------------------------------
USERNAME = "target_account_here"   # display label only, for your reference
USER_ID = "47074278351"            # the account's permanent numeric ID
# ----------------------------------------------------------------------

# The repo is wherever this script lives — no path to configure.
REPO_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(REPO_DIR, "followers.json")


def _load_sessionid() -> str:
    """Read the Instagram sessionid from session.txt (kept out of git) or env."""
    path = os.path.join(REPO_DIR, "session.txt")
    if os.path.exists(path):
        with open(path) as f:
            return f.read().strip()
    return os.environ.get("IG_SESSIONID", "")


def get_count(user_id: str) -> int:
    """Pull the follower count via the leaner users/{id}/info endpoint.

    The full web_profile_info endpoint 400s on some business accounts (a broken
    'business_category' asset). Querying by numeric ID against /info/ returns a
    slimmer JSON that avoids that field entirely.
    """
    ua = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
    session = requests.Session()

    sessionid = _load_sessionid()
    if sessionid:
        session.cookies.set("sessionid", sessionid, domain=".instagram.com")

    session.get("https://www.instagram.com/", headers={"User-Agent": ua}, timeout=20)

    resp = session.get(
        f"https://i.instagram.com/api/v1/users/{user_id}/info/",
        headers={
            "User-Agent": ua,
            "x-ig-app-id": "936619743392459",
            "x-csrftoken": session.cookies.get("csrftoken", ""),
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
        },
        timeout=20,
    )
    resp.raise_for_status()
    return resp.json()["user"]["follower_count"]


def publish(count: int) -> None:
    """Write followers.json and push it only if the number changed."""
    with open(DATA_FILE, "w") as f:
        json.dump(
            {"followers": count, "updated": datetime.now(timezone.utc).isoformat()},
            f,
        )

    def git(*args):
        return subprocess.run(["git", "-C", REPO_DIR, *args])

    git("add", "followers.json")
    # returncode != 0 means there IS a staged change worth committing
    has_change = git("diff", "--cached", "--quiet").returncode != 0
    if has_change:
        git("commit", "-m", f"update follower count: {count}")
        git("push")
        print(f"Published {count} followers.")
    else:
        print(f"No change ({count}). Nothing to push.")


if __name__ == "__main__":
    try:
        publish(get_count(USER_ID))
    except Exception as e:
        # Print and exit non-zero so cron logs show failures clearly.
        print(f"ERROR: {e}")
        raise