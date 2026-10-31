# How fetch.py works

`fetch.py` downloads the newest 300 issues and pull requests (PRs) from **any public
GitHub repo**, along with who replied to them and when. It saves them to that repo's own
cache file, for example `cache_fastapi__fastapi.json` for fastapi/fastapi. Later stages
only read cache files, so they never need to talk to GitHub themselves.

The code is split into small files so each one stays short:

| File | Job |
|---|---|
| `fetch.py` | The part people use: checks the repo name, runs the whole fetch (`fetch_repo`), and the command line. |
| `fetch_steps.py` | The download steps: the list of issues/PRs, then each one's comments and reviews. |
| `simplify.py` | Turns GitHub's big replies into the small dictionaries we save. |
| `github_api.py` | Talks to GitHub: the token, the requests, the error messages. |
| `cache_file.py` | Saves, loads, lists and summarises the cache files. |
| `metrics.py` | Stage 2: works out wait times and contributor numbers from the cache. |
| `metric_helpers.py` | Small building blocks for `metrics.py` (times, bots, first reply). |
| `report_helpers.py` | Prints the results of `metrics.py`, 3 hand-check samples and a plain-English summary. |
| `data_overview.py` | Shows what's really in the cache: association counts and the date range. |
| `health.py` | Turns the metrics into one 0-100 health score. |
| `health_helpers.py` | The small calculations behind the health score. |
| `priority.py` | Stage 5: sorts open items into three maintainer queues with next actions. |
| `priority_helpers.py` | Small facts about one item used by `priority.py` (reason, next action). |
| `config.json` | Settings you edit by hand, such as which labels count as priority. |
| `priority_info.py` | Stage 8: a priority note and next action for every waiting item, from the guidelines or labels. |
| `priority_notes.py` | The small pieces behind `priority_info.py` (waiting items, notes, label match). |
| `guidelines.py` | Turns the repo's CONTRIBUTING file into yes/no checks, and asks the local model to answer them. |
| `contributing_file.py` | Downloads the CONTRIBUTING file's text from GitHub. |
| `local_model.py` | Talks to the local AI model (Gemma) through Ollama, and checks its answers. |

## Running it

```
pip install requests python-dotenv
echo "GITHUB_TOKEN=your_token_here" > .env
python3 fetch.py                                  # fastapi/fastapi, uses saved data if there is any
python3 fetch.py simonw/datasette-cluster-map     # any public repo, saved to its own file
python3 fetch.py pallets/flask --refresh          # ignore saved data and download again
```

**Try a small repo first.** `simonw/datasette-cluster-map` has about 57 issues and PRs, so
it finishes in under a minute. A big repo like fastapi/fastapi makes 400 to 600 requests
and takes about 9 minutes, so run it before the demo, not during it.

**From other Python code** (for example a dashboard):

```python
from fetch import fetch_repo
from cache_file import list_cached_repos

items = fetch_repo("simonw/datasette-cluster-map")         # uses saved data if there is any
items = fetch_repo("pallets/flask", refresh=True)          # always download again
print(list_cached_repos())                                 # ['fastapi/fastapi', 'simonw/...']
```

`metrics.py`, `health.py` and `priority.py` still read **fastapi/fastapi** (the default
repo), because they call `load_cache()` without saying which repo.

## The big picture

1. Check the repo name is safe (`owner/name`).
2. If that repo already has a cache file and you didn't ask to refresh, use it and stop.
3. Otherwise download up to 3 pages of 100 issues/PRs.
4. For each one, download its comments, and for PRs its reviews too.
5. Save to the repo's cache file. If anything went wrong halfway, save what we got first,
   then report the problem in plain English.

## fetch.py

**`read_settings()`** looks at what you typed after `python3 fetch.py`.
`sys.argv` is a list of those words. If a word is `--refresh` we remember that,
and any other word is treated as the repo name. With no words, the repo is
`fastapi/fastapi`. It returns two things: the repo name and `True`/`False` for refresh.

**`is_valid_repo(text)`** is a safety check before the name goes into a web address or a
file name. It's `True` only if the text is exactly two parts joined by one `/`, and each
part is made only of letters, digits, dots, dashes and underscores. So `fastapi/fastapi`
passes, but `fastapi`, `a/b/c`, `owner/re po` and `owner/repo;rm` fail. Parts that are just
`.` or `..` also fail, because in paths and web addresses they mean "this folder" and "go up
a folder". That stops anyone from tricking the program into reading or writing somewhere else.

**`fetch_repo(repo, progress=None, refresh=False)`** is the whole fetch as one function that
other code can call. It checks the name, then uses saved data if there is any (unless
`refresh` is `True`). Otherwise it reads the token, downloads everything, saves it and
returns the list of items. `progress` is optional: if you pass a function, it gets called
after every step as `progress(done, total, message)`, for example
`progress(25, 57, "Fetched replies for 25 of 57")`, which a dashboard could use for a progress
bar. If something goes wrong, it **raises** an error with a plain-English message instead of
crashing with a confusing one. If the problem happens halfway, it saves what it has first
(marked `"complete": false`).

**`print_progress(done, total, message)`** is the progress function the command line uses. It
prints every page, then only every 25 items, so the screen doesn't fill up.

**`main()`** is the command line. It calls `fetch_repo` with `print_progress`. If an error is
raised, it prints `Error: ` and the plain-English message, then exits. Otherwise it prints
the summary.

## fetch_steps.py

**`tell(progress, done, total, message)`** passes a progress update on, but only if someone
gave us a progress function. This saves writing "if progress is not None" everywhere.

**`fetch_item_list(repo, token, progress)`** downloads the list of issues and PRs. GitHub
returns at most 100 per request ("page"), so we ask for page 1, 2 and 3. We stop early if a
page has fewer than 100 items (the repo has no more) or if we already have 300. GitHub's
"issues" list includes PRs too, which is why one request gets both.

**`fetch_replies(repo, token, raw, calls_left)`** fills in the `comments` and `reviews` lists
for one item. GitHub tells us how many comments an item has, so we only ask for comments when
that number is above 0, which saves requests. For PRs we always ask for reviews, because the
comment count doesn't include them. For each comment we keep who wrote it, whether they're a
bot and when. For each review we also keep its state (`APPROVED`, `CHANGES_REQUESTED`,
`COMMENTED`).

**`fetch_all_replies(repo, token, raw_items, calls_left, progress)`** runs `fetch_replies` on
every item. Before each one it checks how many API calls are left: GitHub allows 5,000 an hour,
and if fewer than 20 are left we stop cleanly. If GitHub returns an error, we catch it
(`try` / `except`) and stop. Either way, it returns the items finished so far and a message
saying what went wrong (or `None` if nothing did), so `fetch_repo` can save them. Items that
never got their replies downloaded are left out on purpose, so they don't look like "nobody
replied".

## simplify.py

These functions used to be in `fetch.py`. They moved here when Stage 5 added new
fields, so that `fetch.py` stays short.

**`describe_user(user)`** pulls out two facts about a person: their login name and
whether the account is a `User` or a `Bot`. If someone deleted their GitHub account,
GitHub sends nothing (`None`), so we call them `"ghost"`, which is what the GitHub
website shows.

**`label_names(raw)`** GitHub sends each label as a small dictionary (name, colour,
description). This keeps just the names, such as `["bug", "docs"]`.

**`remove_html_comments(text)`** removes hidden comments like `<!-- Please describe your
change -->`. Many repos' PR templates start with a block of instructions inside one of these.
GitHub doesn't show them on the page, so they aren't the author's words. In fastapi's template,
the hidden block is 392 characters long. The function finds each `<!--`, then the next `-->`,
and keeps only the text outside them. If a comment has no end (because the text was cut short),
everything from `<!--` onward is removed.

**`short_body(raw)`** removes the hidden comments, then keeps the first 800 characters of the
issue or PR text. That's enough to see what it's about without making the cache file huge.
Removing the comments *first* matters: otherwise a long template could fill most of the 800
characters and push the author's real explanation off the end. If the author left the text
blank, GitHub sends `None`, and we save an empty string `""` instead.

**`simplify_item(raw)`** GitHub sends dozens of fields per issue. This keeps only
the ones we need: number, title, whether it's a PR, the author, their
`author_association` (for example `NONE` for outsiders, or `MEMBER` for maintainers),
when it was created and last updated (`updated_at`), open/closed state, whether a PR
is a draft, its label names, and the first 800 characters of its text. An item is a PR
if GitHub included a `pull_request` field in it. It also starts two empty lists,
`comments` and `reviews`, which `fetch_replies` in `fetch_steps.py` fills in.

## github_api.py

**`read_token()`** uses `python-dotenv` to load the `.env` file in the project folder (the
same folder as `github_api.py`, wherever you run the program from), then reads
`GITHUB_TOKEN`. If it's missing, it raises an error saying how to fix that. The token is only
ever put into the request header. It is never printed or saved, and `.env` is listed in
`.gitignore` so it can't be committed by accident.

**`explain_error(status_code)`** turns GitHub's error numbers into plain words:

| Code | Message |
|---|---|
| 401 | Bad GitHub token |
| 403 or 429 | GitHub rate limit reached, try again later |
| 404 | Repo not found, or it is private |

GitHub answers 404 for private repos your token can't see, as well as for repos that don't
exist, so the message mentions both.

**`get_json(path, token)`** is the only place we contact GitHub, and it only ever does GET
(read) requests. It waits 0.1 seconds first so we don't hammer GitHub, then sends the request
with our token. On success it returns the data and the `X-RateLimit-Remaining` header (how many
calls we have left this hour). On failure it **raises** an error with the plain-English
message, so whoever called it decides how to show it.

## cache_file.py

Each repo gets its own cache file. Before this, everything went into one `cache.json`, which
only held one repo at a time.

**`cache_path(repo)`** builds the file name: `fastapi/fastapi` becomes
`cache_fastapi__fastapi.json`. A file name can't contain `/`, so we use two underscores
instead. GitHub usernames can't contain underscores, so the first `__` always marks where the
owner ends. The name is turned into small letters first, because GitHub ignores capitals in
repo names: `FastAPI/FastAPI` and `fastapi/fastapi` are the same repo, so they share one file
instead of keeping two copies of the same data. (`fetch_repo` also turns the name into small
letters before it starts, so the name saved inside the file matches.)

**`find_cache_file(repo)`** decides which file to read: the repo's own cache file if it exists.
For fastapi/fastapi only, if the new file doesn't exist yet, it falls back to the old
`cache.json`, so the data we already downloaded keeps working.

**`cache_exists(repo)`**, **`load_cache(repo)`** and **`save_cache(cache)`** check for, read and
write a repo's cache file. If you leave out `repo`, they use `DEFAULT_REPO` (fastapi/fastapi),
which is why `metrics.py`, `health.py` and `priority.py` didn't need to change. `save_cache`
reads the repo name from inside the data, so it always writes to the right file. `indent=2`
makes the file readable by people too.

**`list_cached_repos()`** looks at the file names in the folder, picks the ones shaped like
`cache_owner__name.json`, and turns each back into `owner/name`. If the old `cache.json` is
there, fastapi/fastapi is included too.

**`has_reply(item)`** answers "did a real person other than the author respond?"
It returns `True` if any comment or review came from a human who isn't the author.
Bots don't count: many repos have a bot that comments on every new PR within
seconds, which would make response times look instant when they aren't.

**`print_summary(cache)`** counts issues, PRs and items with a human reply, then
prints them. If the fetch stopped early, it says so. At the end it calls
`print_label_counts`.

**`print_label_counts(items)`** counts how many items have each label and prints them
A to Z, so the team can choose priority labels for `config.json` from real data.
If the cache was made before labels were saved, it says to run `--refresh`.

## What's in cache.json

```json
{
  "repo": "fastapi/fastapi",
  "fetched_at": "2026-10-30T23:45:00+00:00",
  "complete": true,
  "items": [
    {
      "number": 16634, "title": "...", "is_pr": true,
      "author": "someone", "author_association": "NONE",
      "created_at": "2026-10-30T17:03:57Z", "updated_at": "2026-10-30T17:06:17Z",
      "state": "open", "draft": false, "labels": ["docs"], "body": "first 800 characters...",
      "comments": [{"login": "github-actions[bot]", "user_type": "Bot", "created_at": "..."}],
      "reviews": [{"login": "a-maintainer", "user_type": "User", "state": "APPROVED", "submitted_at": "..."}]
    }
  ]
}
```

---

# Stage 2: how metrics.py works

`metrics.py` reads `cache.json` and turns it into numbers. It makes **no** network
calls, so it runs instantly and works offline. Run it with `python3 metrics.py`
after `fetch.py` has made `cache.json`.

## Words we use

- **Human:** any account whose type isn't `Bot` and whose login doesn't end in `[bot]`.
  Bots like `github-actions[bot]` reply within seconds, so counting them would make
  waits look much shorter than they are.
- **Author:** the person who opened the issue or PR. Their own comments don't count as a reply.
- **Hours:** every timestamp is in UTC (the `Z` at the end means UTC). We subtract
  two timestamps and divide the seconds by 3600.
- **Still waiting:** an **open** item with no answer yet. We don't throw these away.
  We count them and list them with how old they are, because throwing them away would
  hide the worst waits. A **closed** item that never got a reply isn't waiting for
  anyone, so it's left out of both the waits and the still-waiting count.
- **Bot-opened items are left out of every metric.** In fastapi, `pr-submit[bot]`
  and `dependabot[bot]` opened 97 of the 300 items. They aren't newcomers, and
  including them would distort the numbers.

## metrics.py

**`first_response_hours(item)`** finds the first comment on an issue or PR from a
human who isn't the author, and returns how many hours after the item was opened
that comment came. If there's no such comment, it returns `None`, which means
"still waiting".

**`pr_review_wait_hours(item)`** does the same for PR reviews. It looks for the first
review from a human who isn't the author, in any state except `PENDING` (a pending
review is one that hasn't been submitted yet). It skips issues and draft PRs, because
a draft says "not ready for review yet". If there's no such review, it returns `None`.

**`median_first_response(items)`** runs `first_response_hours` on every human-opened
item and gives back three numbers: the **median** (the middle value when all the
waits are sorted), how many items were counted, and how many open items are still
waiting. Closed items with no reply are skipped. We use the median rather than the
average because one item that waited 60 days would drag the average way up.

**`median_review_wait(items)`** does the same with `pr_review_wait_hours`, but only
over PRs that aren't drafts.

**`still_waiting_list(items)`** lists every **open**, human-opened item that has no
human reply, plus every open non-draft PR with no human review. Each entry has the
number, title, author, whether it's a PR, and its age in hours (now minus when it
was opened). The list is sorted so the longest wait comes first.

**`newcomer_retention(items)`** is a **draft definition**. A newcomer is a human
(bot authors are excluded) whose `author_association` is `FIRST_TIME_CONTRIBUTOR`,
`FIRST_TIMER` or `NONE`. `NONE` means GitHub sees no link between that person and the
repo: they have no merged commits there and aren't a member. For each newcomer, we
check if they opened another issue or PR within 30 days of their first one. It returns
how many newcomers there are, how many came back, and the percentage. It only looks at
the items in the cache, not the repo's full history.

Why `NONE` is included: on fastapi, the cache only contains `NONE` (134 items),
`CONTRIBUTOR` (101) and `MEMBER` (65), and never `FIRST_TIME_CONTRIBUTOR` or
`FIRST_TIMER`. With only those two, this found 0 newcomers. With `NONE` added, it
finds 97 newcomers, and 19 of them (19.6%) came back. Two limits to mention to judges:
`NONE` can also include an outsider who has opened issues for years without a merged
commit, and the cache only covers 70.5 days. 30 of the 97 newcomers opened their first
item less than 30 days before the newest item, so they haven't had a full 30 days to
come back yet. The real return rate is probably a bit higher.

**`contributor_funnel(items)`** counts different people at three stages: how many
opened at least one issue, how many opened at least one PR, and how many opened two
or more items in total (repeat contributors). It uses a Python `set`, which is like
a list that ignores duplicates, so each person is only counted once.

**`main()`** loads `cache.json` (or tells you to run `fetch.py` first), works out
every metric, puts the results in one dictionary, and hands it to `print_report`.

## metric_helpers.py

**`parse_time(text)`** turns a GitHub timestamp like `2026-10-28T09:15:00Z` into a
Python `datetime`, so we can subtract two of them.

**`hours_between(start, end)`** subtracts two timestamps and gives back hours.
**`hours_since(start)`** does the same, but uses "right now" as the end.

**`is_human(login, user_type)`** returns `False` for bots and `True` for everyone else,
using the definition above.

**`human_authored(items)`** gives back a new list with the bot-opened items removed.
Every metric starts by calling it. We only store the author's login, not their account
type, so for authors we spot bots by the `[bot]` at the end of the login.

**`is_waiting(item)`** returns `True` if the item is still open. It's one line, but
giving it a name makes the rule "only open items can be waiting" easy to find and
change.

**`first_reply_time(item)`** goes through the item's comments, skips the author's own
and any bots, and remembers the earliest one. **`first_review_time(item)`** does the
same for reviews, and also skips `PENDING` ones.

**`summarise_waits(waits)`** takes a list where each value is either a number of hours
or `None`. It splits them into "counted" and "still waiting" and works out the median.
Both median functions use it, so the logic is written only once.

**`get_age(entry)`** just returns an entry's age. Python's `sort` uses it to know what
to sort the still-waiting list by.

**`came_back(items, author, days)`** gathers all the times one author opened something,
sorts them, and checks if any later one is within `days` days of the first.

## report_helpers.py

**`format_hours(hours)`** shows hours as text such as `7.3 h (0.3 days)`, or `n/a` if
there's no value.

**`kind_name(is_pr)`** gives back `"PR"` or `"Issue"`.

**`pick_samples(items)`** picks three human-opened items worth checking by hand: an
issue that got a reply, a PR that got a review, and an open item with no human reply yet.

**`print_sample(item, repo)`** prints one item in detail: a link to open on GitHub, when
it was created, the first human reply time and review time, and the hours each one
took. Open the link and compare the times yourself to confirm the code is right.

**`print_median(label, summary)`** prints one median line: the median, how many items
were counted, and how many are still waiting.

**`print_plain_summary(results)`** prints the main numbers as plain-English sentences,
such as "Of the items that got a human reply, half got one within 6.9 h". These are
ready to read out to judges.

**`print_report(cache, results)`** prints everything in order: first the data overview
(from `data_overview.py`), then the metrics, the 5 longest-waiting items, newcomers
and the funnel, the 3 hand-check samples, and finally the plain-English summary.

## data_overview.py

This file doesn't measure anything. It shows what the data really contains, so we can
check our definitions make sense before trusting the numbers.

**`association_counts(items)`** counts how many items have each `author_association`
value, such as `NONE: 134`. It counts all items, bots included, because it's
describing the raw data. This is how we found out fastapi never uses
`FIRST_TIME_CONTRIBUTOR`.

**`date_range(items)`** finds the oldest and newest `created_at` in the cache, and
how many days apart they are. This tells you how much history the 300 items cover.
For a busy repo it might be a few weeks, and for a quiet one it might be years.

**`print_overview(items)`** prints both of the above at the top of the report.


---

# health.py: the health score

Run `python3 health.py` to get one number from 0 to 100, plus the four parts it's made
of. It uses the functions in `metrics.py`, so the same rules apply: bot-opened items are
left out, and only open items count as still waiting. Every number in the formula is a
named constant at the top of `health.py`, so changing a weight or a threshold means
changing one line.

## The formula

| Part | Points | Full marks | 0 points |
|---|---|---|---|
| Response: median first human reply | 30 | 24 hours or less | 168 hours (7 days) or more |
| Review: median first human PR review | 20 | 48 hours or less | 336 hours (14 days) or more |
| Newcomer: newcomer items waiting over 7 days | 25 | none of them | all of them |
| Unanswered: open items nobody has answered | 25 | none of them | all of them |

**Response and review parts.** In between full marks and 0, the points fall in a
straight line. For example, a median first response of 96 hours is exactly halfway
between 24 and 168, so it gets half of 30, which is 15 points.

**Newcomer part.** We look at every item opened by a newcomer (`FIRST_TIME_CONTRIBUTOR`,
`FIRST_TIMER` or `NONE`, bots excluded) and work out what share of them are still open
with no reply or review after more than 7 days. The part is worth `25 x (1 - that share)`.

**Unanswered part.** We look at every **open** item opened by a human and work out what
share of them have had **no human reply and no human review at all**. The part is worth
`25 x (1 - that share)`. So if half the open items have been ignored, this part gets 12.5.

**Missing data.** If a part can't be worked out (for example, no PR ever got a review,
or there are no open items), it gets **half marks**. That way, missing data doesn't
make a repo look perfect or terrible.

## Why unanswered items now count

The first version only used medians, and a median only looks at items that **did** get
an answer. If a repo answered 10 items quickly and ignored 90, the median would still be
fast and the score would still look great. That's the opposite of what Community Pulse is
for. The unanswered part fixes this by asking a second question: "of the items that are
open right now, how many has nobody answered?" Ignoring people now lowers the score,
even when the answers that did happen were fast.

## The functions

**`health_parts(items)`** (in `health.py`) works out the four parts. **`health_score(items)`**
adds them up and rounds to one decimal place. **`print_part(label, points, max_points)`**
prints one line like `Review part: 20 / 20`. **`main()`** prints the four parts and the total.

In `health_helpers.py`:

**`sliding_points(hours, full_hours, zero_hours, max_points)`** does the straight-line rule
for the response and review parts, and gives half marks when there's no data.

**`share_points(share, max_points)`** does the "max points x (1 - share)" rule for the
newcomer and unanswered parts. It keeps the answer between 0 and the max, and gives half
marks when there's no data.

**`newcomer_long_wait_share(items, wait_hours)`** finds the share of newcomer items that are
on the still-waiting list and older than `wait_hours`.

**`unanswered_share(items)`** counts the open, human-opened items, counts how many of them
have no human reply and no human review, and divides the two.

## fastapi/fastapi example

```
  Response part:   30 / 30     (median 6.9 h, under 24 h)
  Review part:     20 / 20     (median 24.7 h, under 48 h)
  Newcomer part:   23.9 / 25   (3 of 67 newcomer items stuck for 7+ days)
  Unanswered part: 13.3 / 25   (7 of 15 open items have no human answer at all)
Health score: 87.2 / 100
```

The score went from 98.7 to 87.2. Fastapi answers quickly when it answers, but almost half
of its open items haven't had any human answer yet.

**Limits to mention to judges:** only 15 items are open, so a few items can move the
unanswered part a lot. Items that were **closed** without any human reply still don't count
against the score, because the unanswered part only looks at open items.

---

# Stage 5: priority.py, the maintainer queues

`python3 priority.py` answers the maintainer's question "what should I look at next?" It
reads `cache.json` and `config.json` (no network calls) and sorts open items into three
queues, each entry with a plain-English reason and a next action.

**Before using it:** run this once, so `cache.json` has the new `labels`, `updated_at` and
`body` fields:

```
python3 fetch.py --refresh
```

Then look at the label counts it prints and put the ones that matter in `config.json`, for
example `{"priority_labels": ["bug", "security"]}`. Capital letters don't matter.

## The three queues

Only **open** items opened by **humans** are used. Each item goes in **at most one** queue,
checked in this order (the first rule that matches wins):

1. **Needs attention:** PRs that are drafts, or whose most recent human review asked for
   changes (`CHANGES_REQUESTED`).
2. **Newcomer support:** items from newcomers (`FIRST_TIME_CONTRIBUTOR`, `FIRST_TIMER` or
   `NONE`, the same rule as `metrics.py`) that have no human reply or review yet.
3. **Ready for review:** every other item with no human reply or review yet.

Open items that already got a human answer, and aren't in queue 1, aren't in any queue,
because someone is already talking to the author. Inside each queue, items with a priority
label come first, then the longest wait.

## priority.py

**`choose_queue(item)`** checks the three rules above in order and returns the name of the
first queue that matches, or `None` if the item has already been answered.

**`make_entry(item, config, repo, queue)`** builds the dictionary for one item: number,
title, author, is_pr, days_waiting (since it was opened), is_newcomer, is_priority, queue,
reason, next_action and a link to it on GitHub.

**`priority_then_wait(entry)`** tells Python's `sort` what to compare: first "is it
priority?", then "how many days has it waited?". With `reverse=True`, `True` comes before
`False` and bigger numbers come first, so priority items are on top, longest wait first.

**`build_queues(items, config, repo)`** goes through every open, human-opened item, asks
`choose_queue` where it belongs, builds its entry, then sorts each queue. It returns three
lists: needs attention, newcomer support, ready for review. It takes `repo` as well as
`items` and `config`, because each entry needs the repo name for its GitHub link.

**`print_queue(name, entries)`** prints a queue's count and its top 5 entries: number, days
waiting, reason and next action.

**`check_one_queue(queues)`** is a safety check. It goes through all three queues and makes
sure no item number shows up twice. It prints `Check: each item in only one queue: OK`, or an
error listing the repeated numbers.

**`main()`** loads both files, builds the queues and prints them.

## priority_helpers.py

**`load_config()`** reads `config.json`. If the file is missing, or has no `priority_labels`
list, it uses an empty list, so nothing breaks and no item counts as priority.

**`is_newcomer(item)`** uses the newcomer list from `metrics.py`, so both stages always agree
on who a newcomer is.

**`has_no_answer(item)`** is `True` when no human other than the author has replied **and**
no human has reviewed. It's built from `first_reply_time` and `first_review_time` in
`metric_helpers.py`, so bots and the author's own comments are ignored, just like in Stage 2.

**`latest_review_state(item)`** finds the most recent human review (skipping unsubmitted
`PENDING` ones) and returns its state. Only the latest one matters: if a maintainer asked for
changes and later approved, the PR no longer needs attention.

**`needs_attention(item)`** is `True` for a PR that is a draft, or whose latest review state
is `CHANGES_REQUESTED`.

**`priority_labels_found(item, config)`** lowers the capitals on both sides, then returns the
item's labels that are in the priority list. An old cache with no `labels` field counts as
no labels.

**`make_reason(item, days)`** builds the reason from facts, for example
`Waiting 12.0 days, outside contributor, label: bug`. It turns the GitHub association into
plain words (`NONE` becomes "outside contributor", `MEMBER` becomes "team member", and so on),
adds "draft" or "changes requested" when true, and lists the labels.

**`next_action(item, is_priority)`** picks one action:

| Situation | Next action |
|---|---|
| Draft PR | No action yet; still a draft |
| Latest review asked for changes | Waiting on the author; ping if no update in 7 days |
| PR with no human review | Review this PR |
| Issue from a newcomer, no reply | Welcome and reply to the newcomer |
| Issue, no reply | Reply to the author |

If the item has a priority label, the action starts with `Priority: `.

## fastapi/fastapi example (old cache, no labels yet)

```
Needs attention: 0 items
Newcomer support: 4 items
  #16368, 44.5 days: Waiting 44.5 days, outside contributor
      Next: Review this PR
Ready for review: 3 items
  #16407, 32.1 days: Waiting 32.1 days, team member
      Next: Review this PR
Check: each item in only one queue: OK
```

The 7 items in the newcomer and ready queues are the same 7 unanswered open items that lower
the health score's unanswered part, so the two stages agree.

## What this does NOT do

- **No reviewer matching.** It says "Review this PR" but doesn't suggest *who* should
  review it.
- **No learning.** The rules are fixed and written by hand. Nothing changes based on what
  maintainers did before.
- **No duplicate detection.** Two issues about the same bug show up as two separate entries.
- It also doesn't look at CI checks, and it only sees the items in `cache.json`.

---

# Stage 8: priority notes from the repo's own guidelines

`python3 priority_info.py owner/repo` looks at every item that is still waiting and adds a short
**note** and a **next action**. If the repo has a CONTRIBUTING file, a small AI model running on
your own computer (Gemma, through Ollama) checks each waiting PR against those guidelines. If
that isn't possible, it falls back to the priority labels in `config.json`.

**Everything is optional.** If Ollama isn't running, the repo has no CONTRIBUTING file, or the
model gives a broken answer, it prints a plain message and falls back to labels. It never
crashes, and it never posts anything to GitHub.

## Setting it up (optional)

```
ollama pull gemma3:4b      # once, downloads the model (about 3 GB)
ollama serve               # if Ollama isn't already running
python3 fetch.py owner/repo
python3 priority_info.py owner/repo
```

It writes three files in the project folder:

| File | What's in it |
|---|---|
| `guidelines.json` | The repo name, the CONTRIBUTING link, the Code of Conduct link, and the first 6000 characters of CONTRIBUTING. |
| `checklist.json` | The yes/no checks. **You can edit this by hand**, and your version is used next time. |
| `priority_info.json` | For each waiting item number: source, is_priority, note, next_action. |

## Where the note comes from

For each open, human-opened, non-draft item that is still waiting for a human reply or review:

1. **"guidelines"**: there is a checklist, and the model answered the checks for this PR. The
   item is priority if no check was answered "no". Example note:
   `Meets 4 of 6 guideline checks; missing: includes complete traceback; unclear: version of requests`.
2. Otherwise **"labels"**: the item is priority if it has one of the `priority_labels` from
   `config.json`. Example note: `Priority label: bug`.
3. Otherwise **"none"**: not priority, and no note.

Only the **10 longest-waiting PRs** are sent to the model, because each answer takes a few
seconds on a laptop. Everything else uses the labels fallback.

## local_model.py

**`ask_model(prompt)`** sends a prompt to Ollama at `http://localhost:11434/api/generate` with
model `gemma3:4b`, `"stream": false` (wait for the whole answer) and `"format": "json"` (ask
for JSON back). It waits up to 120 seconds. It turns the reply into Python and returns it. If
Ollama isn't running, the model isn't installed, or the reply isn't valid JSON, it prints a
plain message and returns `None`.

**`as_string_list(answer)`** checks that the model's answer is a list of strings, such as
`["Links an issue", "Has tests"]`. Small models often wrap the list, like
`{"checks": [...]}`, so if the answer is a dictionary with exactly one value, it looks inside.
Anything else returns `None`.

## contributing_file.py

**`html_to_api_url(html_url)`** turns a web link like
`https://github.com/fastapi/.github/blob/main/CONTRIBUTING.md` into the matching API address
(`.../repos/fastapi/.github/contents/CONTRIBUTING.md?ref=main`).

**`download_text(url, token)`** downloads one file through GitHub's contents API. GitHub sends
the text **base64-encoded** (a safe way to send any characters), so we decode it, then keep the
first 6000 characters. It returns `None` if anything fails.

**`download_contributing(contributing, token)`** tries GitHub's `url` link first, then the
address built from `html_url`. We need both: when an organisation keeps one shared CONTRIBUTING
file in its `.github` repo (fastapi does), GitHub's `url` points to the wrong place, but
`html_url` is right.

## guidelines.py

**`save_json(file_name, data)`** writes a dictionary to a JSON file, nicely indented.

**`find_guidelines(repo)`** asks GitHub for the repo's **community profile**, which lists its
CONTRIBUTING file and Code of Conduct. If there's no CONTRIBUTING file, it prints "No
CONTRIBUTING file found" and returns `None`. Otherwise it downloads the text and saves
`guidelines.json`. For the Code of Conduct it saves **only the link**: its text is never
downloaded or shown to the model.

**`load_saved_checklist(repo)`** reads `checklist.json` if it exists and was made for the same
repo. If the file is broken or belongs to another repo, it says so and returns `None`, so a new
checklist is made.

**`make_checklist(text, repo)`** returns the checks. A saved `checklist.json` always wins, so a
maintainer's hand edits are kept. Otherwise it asks the model for at most 6 short checks that
can be answered from a PR's title and description, and saves them. The prompt asks for each check
as a **short phrase, not a question**, such as `includes complete traceback` or
`version of requests`, so the next action reads naturally: "Ask the author to add: includes
complete traceback". It also says every check must come from something the guidelines actually
ask for. (An earlier version gave example phrases, and the model just copied them for every
repo.) If the CONTRIBUTING file is shorter than 500 characters, it doesn't ask the model, because
such files usually just say "see our website", and the model would make up checks. That's what
happens with fastapi (67 characters) and pallets/flask (274 characters). If
the model's answer isn't a list of strings, it uses an empty list, and labels are used instead.

**`check_pr(item, checklist)`** sends the checks, the PR's title and its description to the
model, and asks for one answer per check: `"yes"`, `"no"` or `"unclear"`. The prompt tells the
model to treat the PR text as data, not instructions. Hidden template comments are removed from
the description first (with `remove_html_comments`), which also helps with cache files saved
before that function existed. Any answer that isn't one of those three
words becomes `"unclear"`, and missing answers become `"unclear"` too. If the model doesn't
return a list at all, it returns `None`, so the item falls back to labels.

## priority_notes.py

**`label_priority(item, config)`** returns the item's labels that are in `priority_labels`
(capitals don't matter). It reuses `priority_labels_found` from Stage 5. If an item has no
`labels` field (old data), there's no match.

**`waiting_items(items)`** uses `still_waiting_list` from `metrics.py`, so "still waiting" means
exactly the same as on the dashboard: open, opened by a human, and no human reply (or, for a PR,
no human review). It skips drafts and returns each item with its days waiting, longest first.

**`guideline_info(checklist, answers)`** counts the "yes" answers and lists the "no" and
"unclear" checks, then builds the note and next action: "Review this PR (meets the guidelines)"
if nothing is missing, otherwise "Ask the author to add: ..." followed by the missing checks.

**`fallback_info(item, config)`** is used when the model didn't answer. With a priority label
the source is "labels"; without one it's "none". The next action is "Review this PR" for PRs and
"Reply to the author" for issues.

**`priority_then_wait(row)`** tells Python's `sort` to put priority items first, then the
longest wait.

## priority_info.py

**`build_priority_info(repo, items, config)`** puts it all together. It finds the guidelines,
makes or loads the checklist, then goes through the waiting items, longest wait first. Each of
the first 10 PRs is sent to the model while the model is working. If the model fails once, it
stops asking (`model_working = False`), so a broken model doesn't make you wait for 10 timeouts.
It saves `priority_info.json` and returns the same information.

**`print_report(items, info)`** prints every waiting item, priority first then longest wait,
with its source, note and next action. Then it prints how many items used guidelines, labels or
neither.

**`main()`** reads the repo from the command line (`fastapi/fastapi` if none), checks the name
is safe, checks the repo has been fetched, then builds and prints the report.

## What this does NOT do

- **It reads only the title and description** (the first 800 characters, after hidden template
  comments are removed). The guideline check can't see the code, the tests, the CI results or
  the comments. A PR can "meet the checks" and still be wrong.
- **Its answers are AI suggestions.** A 4-billion-parameter model on a laptop makes mistakes.
  The maintainer always decides, and the note is a hint about what to look at first.
- **The Code of Conduct is never judged.** Only its link is saved. It is never sent to the
  model, and no one is scored against it.
- **It never posts anything to GitHub.** No comments, no labels, no reviews: it only reads.
- **It only checks 10 PRs per run,** to keep the run short.
- **Short CONTRIBUTING files are skipped** (under 500 characters), because they usually just
  link to a website the tool doesn't read. You can write `checklist.json` by hand instead.
- **"Unclear" doesn't count against a PR.** A PR is priority when no check was answered "no",
  so a PR with mostly "unclear" answers is still marked "meets the guidelines". Read the note to
  see how many checks were unclear.

# The weekly Discord digest: digest.py

`python3 digest.py [owner/repo] [--dry-run]` builds a short weekly message from the saved cache
and posts it to a Discord channel. With `--dry-run` it only prints the message and sends nothing,
so always try that first.

## What the message says

- The health score and its word (Healthy, Needs care, At risk).
- The median first reply and the median PR review wait.
- How many open items are still waiting, and how many of those are from newcomers.
- How many newcomers came back within 30 days.
- The 5 items waiting longest, **newcomers first**, each with a link.

The numbers come from the same functions as the dashboard (`pulse_data.py`), so the digest and
the dashboard always agree.

## The functions

**`item_line(row)`** turns one waiting item into a line. Long titles are shortened to 70
characters. Links are wrapped in `< >` so Discord doesn't add a big preview under each one.

**`build_message(repo, items)`** builds the whole message. If it would be longer than Discord's
2,000-character limit, it is cut short.

**`read_webhook()`** reads `DISCORD_WEBHOOK_URL` from `.env`. It checks that the address really is
a Discord webhook, and it never prints the address.

**`send_message(webhook, message)`** posts the message. It turns mentions off
(`allowed_mentions`), so an issue titled "@everyone" can't ping the whole server. If Discord
says no, it prints only the error number.

**`main()`** reads the repo and `--dry-run`, checks the name is safe and the repo has been fetched,
then prints or sends the digest.

## What this does NOT do

- **It doesn't fetch.** Run `python3 fetch.py owner/repo --refresh` first for fresh numbers.
- **It doesn't run by itself every week.** Run it by hand, or schedule it (for example with cron).
- **It never posts anything to GitHub.** It only reads the saved cache, and posts only to Discord.
