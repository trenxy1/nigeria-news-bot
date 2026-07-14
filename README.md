# Nigeria News Bot — Phone-Only Setup (No Laptop Needed)

This runs on **GitHub's free cloud computers**, not your device. You do the setup
through the GitHub app or your phone's browser; after that, it runs itself daily.
You'll only check in to review videos and approve or fix things.

The pipeline: RSS headlines → Groq (free AI, writes the script) → edge-tts (free
voiceover) → Pexels (free images) → video assembly → YouTube upload. All of it
runs on GitHub's servers on a timer.

## What you need on your phone
- The **GitHub app** (or use github.com in your browser) — you already have an account (`trenxy1`)
- A browser, for a few one-time sign-ups (Groq, Pexels, Google Cloud)
- 20-30 minutes for setup, spread across a few sessions is fine

## Step 1 — Create the repo

1. On github.com, create a **new repository** — call it `nigeria-news-bot`. Private is fine.
2. Upload all the files I gave you (config.py, main.py, the others, and the
   `.github/workflows/daily-news.yml` file — make sure that folder structure
   `.github/workflows/` is preserved) into that repo. You can do this from the
   GitHub mobile web view: repo → Add file → Upload files.

## Step 2 — Get your free API keys

- **Gemini** (writes the news scripts, primary): https://aistudio.google.com/apikey → sign in with Google → create key
- **Groq** (fallback, only used if Gemini fails): https://console.groq.com/keys → sign up → create key — optional but recommended as a backup
- **Pexels** (free stock images): https://www.pexels.com/api/ → sign up → copy key

## Step 3 — Add keys as GitHub Secrets

In your repo: **Settings → Secrets and variables → Actions → New repository secret**

Add:
- `GEMINI_API_KEY` → paste your Gemini key
- `GROQ_API_KEY` → paste your Groq key (optional fallback — pipeline still works without it, just with one less safety net)
- `PEXELS_API_KEY` → paste your Pexels key

(Leave `YOUTUBE_TOKEN_JSON` for Step 5 — you don't have it yet.)

## Step 4 — Test the pipeline manually (before touching YouTube)

Repo → **Actions tab** → select "Daily Nigeria News Video" → **Run workflow**
(this is the `workflow_dispatch` trigger — it lets you run it on demand instead
of waiting for the next scheduled run).

This first run will fail at the upload step (no YouTube token yet) — that's
expected. What matters: check the run log. Did headline fetch work? Did the
script generate? Did the video render? Click into the "Upload video as workflow
artifact" step afterward — you can download the MP4 straight from there and
watch it on your phone before YouTube is even involved.

If something fails, the log tells you which step and why — fix that one thing
(usually a missing secret or a bad RSS feed URL in `config.py`) and re-run.

## Step 5 — One-time YouTube authorization

This is the one part that needs an interactive login, and GitHub Actions can't
do interactive logins by itself. Use **GitHub Codespaces** instead — it's a full
coding environment that runs in your phone's browser, free for personal use
(60 free hours/month), no install needed.

1. Go to https://console.cloud.google.com/ → create a project → enable
   "YouTube Data API v3" → Credentials → Create Credentials → OAuth client ID
   → type "Desktop app" → download the JSON.
2. In your repo (mobile browser): tap the green **Code** button → **Codespaces**
   tab → **Create codespace on main**. This opens VS Code in your browser.
3. In the Codespace, upload the downloaded JSON as `client_secret.json` in the
   repo root (drag-and-drop works, or use the file explorer's upload button).
4. Open the Codespace terminal (bottom panel) and run:
   ```
   pip install -r requirements.txt
   ```
   Then, since Codespaces can't pop open a real browser window for the Google
   login, run this instead — it prints a URL you open on your phone to log in:
   ```
   python -c "
   import google_auth_oauthlib.flow, config
   flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
       config.YOUTUBE_CLIENT_SECRET_FILE, ['https://www.googleapis.com/auth/youtube.upload'])
   creds = flow.run_console()
   open(config.YOUTUBE_TOKEN_FILE, 'w').write(creds.to_json())
   print(open(config.YOUTUBE_TOKEN_FILE).read())
   "
   ```
   Open the printed URL, log into the YouTube channel you want to upload to,
   approve, copy the code back into the terminal when prompted.
5. The command prints the contents of `youtube_token.json` at the end — copy
   that whole JSON string.
6. Back in repo **Settings → Secrets → Actions**, add a new secret named
   `YOUTUBE_TOKEN_JSON` and paste that JSON as the value.
7. Delete the Codespace when done (Codespaces tab → your codespace → delete) so
   you don't burn free hours sitting idle. **Do not commit `client_secret.json`
   or `youtube_token.json` to the repo** — they're credentials, not code.

## Step 6 — Go live

Run the workflow manually once more (Step 4's method). It should now fetch,
write, voice, illustrate, render, AND upload — landing on YouTube as
**unlisted** (check it before making it public). Once you're happy with output
quality over a few manual runs, the `cron` schedule already in the workflow
file has it set to run automatically twice a day — 6 AM and 6 PM WAT — no
further action needed from you.

## Monitoring from your phone

- GitHub app → your repo → **Actions** tab shows every run, pass/fail, and logs
- Failed runs send you a notification (GitHub app notifications, on by default)
- Each run keeps the video as a downloadable artifact for 7 days, so you can
  always pull down and rewatch what got uploaded

## Costs — what's actually free vs. what has limits

| Service | Free tier | What happens if you exceed it |
|---|---|---|
| GitHub Actions | 2,000 min/month (private repo) or unlimited (public repo) | At 2 runs/day (~10 min each), that's ~600 min/month — well inside even the private-repo limit |
| Gemini | ~1,500 requests/day free | Falls back to Groq automatically |
| Groq (fallback) | Generous free tier, rate-limited | Both providers down = that run fails, next scheduled run retries |
| Pexels | 200 requests/hour, 20,000/month | Requests fail until reset |
| edge-tts | Free, no limit (Microsoft's public service) | — |
| YouTube Data API | 10,000 quota units/day (~6 uploads/day) | 2 uploads/day uses well under a third of daily quota |

Two videos a day sits comfortably inside every one of these limits. If you later
push to 4+ videos/day or add a second channel, that's when you'd start
watching quota more closely.

## Things to actually watch for

- **First videos will be rough.** Review manually (unlisted) for a few days
  before trusting `--upload` to go straight to public-facing use unattended.
- **RSS feed URLs change.** If a source's feed breaks, the Action log will show
  a warning for that source — update the URL in `config.py`.
- **Don't screenshot other outlets' photos/footage.** Stick to Pexels stock
  images — that's what `image_fetch.py` already does, and it's the safe,
  copyright-clean path.
  
