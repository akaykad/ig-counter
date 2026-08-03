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
USERNAME = "thapletcom"   # the public account you want to track
# ----------------------------------------------------------------------

# The repo is wherever this script lives — no path to configure.
REPO_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(REPO_DIR, "followers.json")


def get_count(username: str) -> int:
    """Hit Instagram's public web endpoint and pull the follower count."""
    resp = requests.get(
        "https://www.instagram.com/api/v1/users/web_profile_info/",
        params={"username": username},
        headers={
            # public web-app id Instagram's own website sends
            "x-ig-app-id": "936619743392459",
            # a real browser User-Agent is required or the request is refused
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        },
        timeout=20,
    )
    resp.raise_for_status()
    return resp.json()["data"]["user"]["edge_followed_by"]["count"]


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
        publish(get_count(USERNAME))
    except Exception as e:
        # Print and exit non-zero so cron logs show failures clearly.
        print(f"ERROR: {e}")
        raise
