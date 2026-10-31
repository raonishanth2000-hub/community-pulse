# Community Pulse

Community Pulse is a self-hostable tool for open-source maintainers that reads a GitHub
repo's latest 300 issues and pull requests and measures how long newcomers wait for a human
reply or review. It shows the results on a Streamlit dashboard and sends a weekly Discord
digest, so maintainers can see who is waiting and act on it.

Built by **Git Guardians** (Nishanth, Shweta, Krishna) during a 12-hour hackathon.

## The four metrics

| Metric | What it means |
|---|---|
| **Median first response** | Hours from when an issue or PR is opened until the first comment by a human who isn't the author. |
| **Median PR review wait** | Hours from when a (non-draft) PR is opened until its first human review. |
| **Newcomer retention** | Share of newcomers who opened another issue or PR within 30 days of their first one. |
| **Repeat contributors** | Number of people who opened two or more issues or PRs. |

Bots (like `dependabot[bot]`) are left out of every metric, and only open items count as
"still waiting". The metrics also feed a 0-100 **health score** (`python3 health.py`) and three
maintainer **priority queues** (`python3 priority.py`).

## Setup

1. Clone the repo and go into it:

   ```
   git clone https://github.com/raonishanth2000-hub/community-pulse.git
   cd community-pulse
   ```

2. Install the dependencies:

   ```
   pip3 install -r requirements.txt
   ```

3. Create your `.env` file from the example, then open `.env` and replace
   `paste_your_token_here` with your own GitHub token:

   ```
   cp .env.example .env
   ```

   A fine-grained token with **read-only access to public repositories** is enough. Community
   Pulse only ever reads from GitHub. `.env` is listed in `.gitignore`, so your token is never
   committed.

4. Download the data (the latest 300 issues and PRs, with their replies). The first run takes a
   few minutes for a busy repo. Later runs use the saved copy unless you add `--refresh`:

   ```
   python3 fetch.py                    # fastapi/fastapi by default
   python3 fetch.py owner/repo         # any public repo
   python3 fetch.py owner/repo --refresh
   ```

5. Open the dashboard:

   ```
   streamlit run dashboard.py
   ```

6. Preview the weekly Discord digest without sending it:

   ```
   python3 digest.py --dry-run
   ```

## Discord webhook

The digest is posted with a Discord webhook. To set one up:

1. In Discord, open **Server Settings → Integrations → Webhooks → New Webhook**, choose the
   channel, and click **Copy Webhook URL**.
2. Add it to your `.env` file on its own line:

   ```
   DISCORD_WEBHOOK_URL=paste_your_webhook_url_here
   ```

Treat the webhook URL like a password: anyone who has it can post in that channel. It belongs
only in `.env`, never in the code or in git.

## AI tools used

- **Claude** (Anthropic): coding assistant used to write and explain the code.
- _Placeholder: add any other tool the team uses here (for example Stitch or Gemma), with what it was used for._

## Known limits and next steps

- **Small samples.** Only the latest 300 issues and PRs are read, so some numbers (especially
  the PR review wait) can rest on a small number of items.
- **The newcomer definition is a draft.** A newcomer is an author GitHub marks as
  `FIRST_TIME_CONTRIBUTOR`, `FIRST_TIMER` or `NONE`. `NONE` can also include long-time outsiders
  who never had a commit merged.
- **No "Waiting on Checks" status.** Community Pulse doesn't read CI results, so it can't tell
  when a PR is waiting on failing tests.
- **No reviewer matching.** The queues say "Review this PR" but don't suggest who should
  review it.

## Learn more

`EXPLAIN.md` is a plain-English tour of every file and function, written for beginners.

## License

MIT. See `LICENSE`.
