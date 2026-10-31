# digest.py - The weekly Discord digest: health score, median waits, and who is still waiting
# (newcomers first), posted to a Discord channel with a webhook. It reads the saved cache only.
# Usage: python3 digest.py [owner/repo] [--dry-run]   (--dry-run prints it and sends nothing)
# The webhook address comes from .env (DISCORD_WEBHOOK_URL) and is never printed.

import os
import sys

import requests
from dotenv import load_dotenv

from cache_file import DEFAULT_REPO, cache_exists, load_cache
from fetch import is_valid_repo
from github_api import ENV_FILE
from pulse_data import health_label, summary, waiting_rows
from report_helpers import format_hours

TOP_COUNT = 5            # how many waiting items to list
TITLE_LENGTH = 70        # longer titles are shortened, so the message stays readable
DISCORD_LIMIT = 2000     # Discord refuses messages longer than this
WEBHOOK_STARTS = ("https://discord.com/api/webhooks/", "https://discordapp.com/api/webhooks/")


# One line for a waiting item. Links are wrapped in < > so Discord doesn't add a big preview.
# In: a row from pulse_data.waiting_rows. Out: text.
def item_line(row):
    title = row["title"]
    if len(title) > TITLE_LENGTH:
        title = title[:TITLE_LENGTH - 3] + "..."
    who = row["type"]
    if row["newcomer"]:
        who = who + ", newcomer"
    return ("• #" + str(row["number"]) + " " + title + " (" + who + ", "
            + str(row["days"]) + " days) <" + row["link"] + ">")


# Builds the whole digest message. In: repo and items. Out: the message text.
def build_message(repo, items):
    numbers = summary(items)
    word, status = health_label(numbers["score"])
    rows = waiting_rows(items, repo)
    newcomers = []
    others = []
    for row in rows:
        if row["newcomer"]:
            newcomers.append(row)
        else:
            others.append(row)
    lines = ["**Community Pulse weekly digest: " + repo + "**",
             "Health score: **" + str(round(numbers["score"])) + " / 100** (" + word + ")",
             "• Median first reply: " + format_hours(numbers["first"]["median_hours"]),
             "• Median PR review wait: " + format_hours(numbers["review"]["median_hours"]),
             "• Still waiting: " + str(len(rows)) + " open items (" + str(len(newcomers)) + " from newcomers)",
             "• Newcomers who came back within 30 days: " + str(numbers["retention"]["percent"] or 0) + "%",
             ""]
    if len(rows) == 0:
        lines.append("Nobody is waiting for a reply or review. Nice work!")
    else:
        lines.append("**Waiting longest (newcomers first):**")
        for row in (newcomers + others)[:TOP_COUNT]:
            lines.append(item_line(row))
    dates = numbers["dates"]
    lines.append("")
    lines.append("_From the latest issues and PRs, " + dates["oldest"][:10] + " to " + dates["newest"][:10] + "._")
    message = "\n".join(lines)
    if len(message) > DISCORD_LIMIT:
        message = message[:DISCORD_LIMIT - 3] + "..."
    return message


# Reads the webhook address from .env. In: nothing. Out: the address, or None if missing or
# not a Discord webhook. The address itself is never printed.
def read_webhook():
    load_dotenv(ENV_FILE)
    webhook = os.getenv("DISCORD_WEBHOOK_URL")
    if not webhook:
        print("No DISCORD_WEBHOOK_URL found. Add it to your .env file (see the README).")
        return None
    if not webhook.startswith(WEBHOOK_STARTS):
        print("DISCORD_WEBHOOK_URL doesn't look like a Discord webhook address. Check your .env file.")
        return None
    return webhook


# Posts the message to Discord. "allowed_mentions" is empty, so a title containing
# @everyone can't ping the whole server. In: webhook and message. Out: True if it was sent.
def send_message(webhook, message):
    body = {"content": message, "allowed_mentions": {"parse": []}}
    try:
        response = requests.post(webhook, json=body, timeout=15)
    except requests.RequestException:
        print("Could not reach Discord. Check your internet connection.")
        return False
    if response.status_code not in (200, 204):
        print("Discord said error " + str(response.status_code) + ". Check the webhook in your .env file.")
        return False
    return True


# Reads the repo and --dry-run from the command line, builds the digest, then prints or sends it.
def main():
    dry_run = "--dry-run" in sys.argv
    repo = DEFAULT_REPO
    for word in sys.argv[1:]:
        if not word.startswith("--"):
            repo = word
    if not is_valid_repo(repo):
        print("'" + repo + "' is not a valid repo name. Use owner/name, like fastapi/fastapi.")
        sys.exit(1)
    repo = repo.lower()
    if not cache_exists(repo):
        print("No saved data for " + repo + " yet. Run python3 fetch.py " + repo + " first.")
        sys.exit(1)
    message = build_message(repo, load_cache(repo)["items"])
    if dry_run:
        print(message)
        print("\n(Dry run: nothing was sent. " + str(len(message)) + " of " + str(DISCORD_LIMIT) + " characters.)")
        return
    webhook = read_webhook()
    if webhook is None or not send_message(webhook, message):
        sys.exit(1)
    print("Digest for " + repo + " sent to Discord.")


if __name__ == "__main__":
    main()
