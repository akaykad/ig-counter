# Instagram Follower Counter (free, self-hosted)

A live follower counter for any **public** Instagram account.
Your home device scrapes the count on a schedule and pushes it to this repo;
GitHub Pages serves the page. Total cost: $0.

## Files
- `scraper.py` — runs on your device, fetches the count, commits `followers.json`
- `index.html` — the public page (served by GitHub Pages)
- `followers.json` — the current number (updated automatically)
- `requirements.txt` — Python dependency (`requests`)

---

## Setup (about 15 minutes)

### 1. Create the repo on GitHub
1. Go to https://github.com/new
2. Name it e.g. `ig-counter`, set it **Public**, click **Create repository**.

### 2. Put these files in the repo
On your home device (the one that will stay on):
```bash
git clone https://github.com/YOUR_USERNAME/ig-counter.git
cd ig-counter
# copy scraper.py, index.html, followers.json, requirements.txt into this folder
```

### 3. Set the target account
Open `scraper.py` and change one line:
```python
USERNAME = "target_account_here"
```

### 4. Install Python dependency
```bash
pip install -r requirements.txt        # or: pip3 install -r requirements.txt
```

### 5. Let the device push to GitHub without a password
The cron job runs unattended, so git must not prompt. Easiest way — a token:
1. Go to https://github.com/settings/tokens?type=beta (fine-grained token)
2. **Generate new token** → give it a name, set **Repository access → Only select
   repositories → your `ig-counter`**, and under **Permissions → Repository →
   Contents** choose **Read and write**. Generate and copy it.
3. Tell git to remember it on this device:
```bash
git config --global credential.helper store
```
   The next `git push` will ask for username + password — paste the **token** as
   the password. Git saves it, so future pushes are silent.

### 6. Test it once, by hand
```bash
python scraper.py        # or python3 scraper.py
```
Expected: `Published <number> followers.` and a new commit on GitHub.
If it says the push failed, redo step 5. If it errors on the fetch, see
Troubleshooting below.

### 7. Turn on GitHub Pages
1. Repo → **Settings** → **Pages**
2. **Source: Deploy from a branch**, Branch: **main**, folder: **/ (root)** → Save.
3. Wait ~1 minute. Your counter is live at:
   `https://YOUR_USERNAME.github.io/ig-counter/`

### 8. Schedule it
**Linux / macOS** — run `crontab -e` and add (updates hourly):
```
0 * * * * /usr/bin/python3 /full/path/to/ig-counter/scraper.py >> /full/path/to/ig-counter/log.txt 2>&1
```
Use the full path (run `which python3` and `pwd` to get them).

**Windows** — use Task Scheduler: create a task that runs
`python C:\path\to\ig-counter\scraper.py` on an hourly trigger.

**Android** — install Termux, `pkg install python git`, then use the
`termux-job-scheduler` package or a `cron` package to run it hourly.

Done. The page updates itself as long as the device is on.

---

## Troubleshooting

- **Fetch fails / 401 / empty response:** Instagram occasionally changes this
  unofficial endpoint. It usually still works from a residential IP; if it
  stops, the `get_count()` function in `scraper.py` is the part to update.
- **Works by hand but not from cron:** cron has a minimal environment. Always
  use **absolute paths** to python and the script, and check `log.txt`.
- **Push asks for a password every time:** step 5 didn't stick — rerun
  `git config --global credential.helper store` and push once manually.
- **Page shows 0:** the first scrape hasn't run yet, or the last push failed.

## Notes
- Only **public** accounts work. Private accounts expose no count.
- Keep polling reasonable (hourly is plenty). Don't hammer it.
