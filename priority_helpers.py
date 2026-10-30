# priority_helpers.py - Small facts about one item, used by priority.py.
# Reuses the Stage 2 helpers (human check, newcomer rule, first reply and review)
# instead of rewriting them.

import json
import os

from metric_helpers import first_reply_time, first_review_time, is_human, parse_time
from metrics import NEWCOMER_TYPES

CONFIG_FILE = "config.json"

# Plain-English words for GitHub's author_association values, used in the "reason" text.
AUTHOR_WORDS = {"NONE": "outside contributor", "FIRST_TIME_CONTRIBUTOR": "first-time contributor",
                "FIRST_TIMER": "first-time GitHub user", "CONTRIBUTOR": "past contributor",
                "COLLABORATOR": "collaborator", "MEMBER": "team member", "OWNER": "repo owner"}


# Reads config.json. In: nothing. Out: dictionary that always has "priority_labels" (a list).
# A missing file, or a file without the list, just means "no priority labels".
def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {"priority_labels": []}
    with open(CONFIG_FILE) as file:
        config = json.load(file)
    if "priority_labels" not in config:
        config["priority_labels"] = []
    return config


# The newcomer rule from metrics.py. In: one item. Out: True or False.
def is_newcomer(item):
    return item["author_association"] in NEWCOMER_TYPES


# True if no human other than the author has replied or reviewed yet. In: item. Out: True/False.
def has_no_answer(item):
    return first_reply_time(item) is None and first_review_time(item) is None


# Finds the state of the most recent human review (PENDING ones are skipped).
# In: one item. Out: a state like "APPROVED" or "CHANGES_REQUESTED", or None if no reviews.
def latest_review_state(item):
    latest_time = None
    latest_state = None
    for review in item["reviews"]:
        if review["state"] == "PENDING" or review["submitted_at"] is None:
            continue
        if not is_human(review["login"], review["user_type"]):
            continue
        if latest_time is None or parse_time(review["submitted_at"]) > parse_time(latest_time):
            latest_time = review["submitted_at"]
            latest_state = review["state"]
    return latest_state


# Checks if a PR is a draft or its latest human review asked for changes.
# In: one item. Out: True or False (always False for issues).
def needs_attention(item):
    if not item["is_pr"]:
        return False
    return item["draft"] or latest_review_state(item) == "CHANGES_REQUESTED"


# Finds which of the item's labels are priority labels (capital letters don't matter).
# In: item and config. Out: list of matching label names. Old caches have no labels.
def priority_labels_found(item, config):
    wanted = []
    for name in config["priority_labels"]:
        wanted.append(name.lower())
    found = []
    for name in item.get("labels", []):
        if name.lower() in wanted:
            found.append(name)
    return found


# Builds the plain-English "reason", e.g. "Waiting 12.0 days, outside contributor, label: bug".
# In: item and days waiting. Out: text.
def make_reason(item, days):
    parts = ["Waiting " + str(days) + " days"]
    parts.append(AUTHOR_WORDS.get(item["author_association"], "contributor"))
    if item["is_pr"] and item["draft"]:
        parts.append("draft")
    elif item["is_pr"] and latest_review_state(item) == "CHANGES_REQUESTED":
        parts.append("changes requested")
    labels = item.get("labels", [])
    if len(labels) > 0:
        parts.append("label: " + ", ".join(labels))
    return ", ".join(parts)


# Decides what a maintainer should do next. In: item and True/False for priority. Out: text.
def next_action(item, is_priority):
    if item["is_pr"] and item["draft"]:
        action = "No action yet; still a draft"
    elif item["is_pr"] and latest_review_state(item) == "CHANGES_REQUESTED":
        action = "Waiting on the author; ping if no update in 7 days"
    elif item["is_pr"]:
        action = "Review this PR"
    elif is_newcomer(item):
        action = "Welcome and reply to the newcomer"
    else:
        action = "Reply to the author"
    if is_priority:
        action = "Priority: " + action
    return action
