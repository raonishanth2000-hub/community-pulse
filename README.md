# Community Pulse

Community Pulse is a self-hostable tool for open-source maintainers that reads a GitHub
repo's latest 300 issues and pull requests and measures how long newcomers wait for a human
reply or review. It shows the results on a Streamlit dashboard, with a health score, maintainer
queues and a ready-to-share weekly summary, so maintainers can see who is waiting and act on it.

Built by **Git Guardians** (Nishanth, Shweta, Krishna) during a 12-hour hackathon.

**Live demo:** _add the Streamlit Community Cloud link here._ The demo shows saved data for
`fastapi/fastapi`.

## The four metrics

| Metric | What it means |
|---|---|
| **Median first response** | Hours from when an issue or PR is opened until the first comment by a human who isn't the author. |
| **Median PR review wait** | Hours from when a (non-draft) PR is opened until its first human review. |
| **Newcomer retention** | Share of newcomers who opened another issue or PR within 30 days of their first one. |
| **Repeat contributors** | Number of people who opened two or more issues or PRs. |

Bots (like `dependabot[bot]`) are left out of every metric, and only open items count as
"still waiting". A **newcomer** is an author GitHub marks as `FIRST_TIME_CONTRIBUTOR`,
`FIRST_TIMER` or `NONE` (no link to the repo yet).

## Health score

The metrics are combined into a 0-100 score (`python3 health.py`):

| Part | Points | Full marks when |
|---|---|---|
| Fast first reply | 30 | median first reply is 24 h or less (0 points at 7 days) |
| Fast PR review | 20 | median PR review wait is 48 h or less (0 points at 14 days) |
| Newcomers not left waiting | 25 | no newcomer item has waited over 7 days |
| Few unanswered open items | 25 | every open item has had a human reply or review |

A part with no data gets half marks. 80 or more is **Healthy**, 50 to 79 **Needs care**, and
under 50 **At risk**.

## The dashboard

`streamlit run pulse_dashboard.py` opens it in your browser. It has seven tabs:

| Tab | What it shows |
|---|---|
| **Overview** | The four metrics, the parts of the health score, and a chart of how fast people hear back. |
| **Health score** | How each part is worked out, and a **What if?** panel: move sliders to see how the score would change. |
| **Waiting** | Every open item still waiting for a reply or review, longest first, with links. |
| **Maintainer queues** | Three to-do lists: *Newcomer support*, *Ready for review* and *Needs attention*. |
| **Contributors** | A funnel: who opened an issue, who opened a PR, who came back. |
| **Weekly digest** | A short weekly summary (score, waits, who is waiting longest) with a copy button, to paste into a team chat. |
| **Gemma notes** | Checks waiting PRs against the repo's CONTRIBUTING guidelines with a local AI model (see below). |

The sidebar lets you switch repos, **add any public repo** (it fetches the data for you), and
filter the waiting list (newcomers only, issues or PRs, minimum days, search).

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

5. Open the dashboard. It opens in your browser at `http://localhost:8501`:

   ```
   streamlit run pulse_dashboard.py
   ```

## Command-line tools

Each one reads the saved data and prints its results. The first three use `fastapi/fastapi`;
the last two take `owner/repo` too (the dashboard shows all of these for any repo).

```
python3 metrics.py                       # the four metrics, with sample items to check by hand
python3 health.py                        # the health score and its four parts
python3 priority.py                      # the three maintainer queues
python3 digest.py owner/repo --dry-run   # the weekly summary, as plain text
python3 priority_info.py owner/repo      # guideline notes from Gemma (needs Ollama, see below)
```

## Optional: guideline notes with Gemma (local AI)

Community Pulse can read a repo's CONTRIBUTING file, turn it into short yes/no checks, and check
waiting PRs against them. It uses **Gemma** (`gemma3:4b`), a small AI model that runs on your own
computer through [Ollama](https://ollama.com), so nothing is sent to an online AI service.

1. Install Ollama, then download the model:

   ```
   ollama pull gemma3:4b
   ```

2. With Ollama running, open the **Gemma notes** tab and click **Run Gemma on waiting PRs**, or
   run `python3 priority_info.py owner/repo`.

If Ollama isn't running, everything else still works, and the notes fall back to priority labels
(set in `config.json`). The Code of Conduct is never sent to the model; only its link is saved.

## Hosting on Streamlit Community Cloud

The dashboard runs on [Streamlit Community Cloud](https://share.streamlit.io) straight from this
repo, using `pulse_dashboard.py` as the main file. `requirements.txt` pins the versions it was
tested with. To let visitors use **Add a repo**, add your token under **Manage app → Settings →
Secrets**:

```
GITHUB_TOKEN = "your_token_here"
```

The hosted app can't reach Ollama, so the Gemma notes tab only works when you run the dashboard
on your own computer.

## AI tools used

- **Claude** (Anthropic): coding assistant used to write and explain the code.
- **Gemma** (Google, `gemma3:4b` through Ollama): runs inside the product, turning CONTRIBUTING
  files into checks and checking PRs against them.
- _Placeholder: add any other tool the team uses here (for example Stitch), with what it was used for._

## Known limits and next steps

- **Small samples.** Only the latest 300 issues and PRs are read, so some numbers (especially
  the PR review wait) can rest on a small number of items.
- **The newcomer definition is a draft.** `NONE` can also include long-time outsiders who never
  had a commit merged, so the newcomer count may be a little high.
- **Gemma's notes are suggestions.** It reads only a PR's title and description (not the code,
  tests or CI), checks up to 10 PRs per run, and skips CONTRIBUTING files under 500 characters
  (they usually just link to a website).
- **No "Waiting on Checks" status.** Community Pulse doesn't read CI results, so it can't tell
  when a PR is waiting on failing tests.
- **No reviewer matching.** The queues say "Review this PR" but don't suggest who should
  review it.
- **Next step: post the weekly summary to Discord automatically.** `digest.py` already has the
  code for a Discord webhook, but it hasn't been set up or tried with a real one yet. For now the
  summary is shared by hand from the Weekly digest tab.

## Learn more

`EXPLAIN.md` is a plain-English tour of every file and function, written for beginners.
`EXPLAIN_pulse_dashboard.md` does the same for the dashboard, including its colours and animations.

## License

MIT. See `LICENSE`.
