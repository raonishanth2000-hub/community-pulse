# priority.py - Stage 5 of Community Pulse. Usage: python3 priority.py
# Sorts open, human-opened items into three maintainer queues, each with a reason
# and a next action. Reads cache.json and config.json only (no network calls).

import sys

from cache_file import cache_exists, load_cache
from metric_helpers import hours_since, human_authored, is_waiting
from priority_helpers import (has_no_answer, is_newcomer, load_config, make_reason,
                              needs_attention, next_action, priority_labels_found)

QUEUE_NAMES = ["Needs attention", "Newcomer support", "Ready for review"]
TOP_COUNT = 5  # how many entries to print per queue


# Decides which queue an item goes in, checking the three rules in order.
# In: one open item. Out: the queue name, or None if it's already been answered.
def choose_queue(item):
    if needs_attention(item):
        return "Needs attention"
    if not has_no_answer(item):
        return None
    if is_newcomer(item):
        return "Newcomer support"
    return "Ready for review"


# Builds one queue entry with everything the dashboard or digest might show.
# In: item, config, repo name, queue name. Out: dictionary.
def make_entry(item, config, repo, queue):
    days = round(hours_since(item["created_at"]) / 24, 1)
    is_priority = len(priority_labels_found(item, config)) > 0
    return {"number": item["number"], "title": item["title"], "author": item["author"],
            "is_pr": item["is_pr"], "days_waiting": days, "is_newcomer": is_newcomer(item),
            "is_priority": is_priority, "queue": queue, "reason": make_reason(item, days),
            "next_action": next_action(item, is_priority),
            "url": "https://github.com/" + repo + "/issues/" + str(item["number"])}


# Used for sorting: priority items first (True sorts above False), then longest wait.
# In: one entry. Out: a pair of values for Python's sort to compare.
def priority_then_wait(entry):
    return (entry["is_priority"], entry["days_waiting"])


# Puts every open, human-opened item into at most one of the three queues.
# In: items, config, repo name. Out: three lists of entries
# (needs attention, newcomer support, ready for review), each sorted.
def build_queues(items, config, repo):
    queues = {}
    for name in QUEUE_NAMES:
        queues[name] = []
    for item in human_authored(items):
        if not is_waiting(item):
            continue
        queue = choose_queue(item)
        if queue is not None:
            queues[queue].append(make_entry(item, config, repo, queue))
    for name in QUEUE_NAMES:
        queues[name].sort(key=priority_then_wait, reverse=True)
    return queues["Needs attention"], queues["Newcomer support"], queues["Ready for review"]


# Prints one queue's count and its top entries. In: queue name and entries. Out: nothing.
def print_queue(name, entries):
    print("")
    print(name + ": " + str(len(entries)) + " items")
    for entry in entries[:TOP_COUNT]:
        print("  #" + str(entry["number"]) + ", " + str(entry["days_waiting"]) + " days: " + entry["reason"])
        print("      Next: " + entry["next_action"])


# Checks that no item number appears in more than one queue, and prints the result.
# In: a list of the three queues. Out: nothing (it prints).
def check_one_queue(queues):
    seen = []
    repeats = []
    for queue in queues:
        for entry in queue:
            if entry["number"] in seen:
                repeats.append(entry["number"])
            seen.append(entry["number"])
    if len(repeats) == 0:
        print("")
        print("Check: each item in only one queue: OK")
    else:
        print("ERROR: these items are in more than one queue: " + str(repeats))


# Loads cache.json and config.json, builds the queues, and prints them.
def main():
    if not cache_exists():
        print("No cache.json yet. Run python3 fetch.py first.")
        sys.exit(1)
    cache = load_cache()
    config = load_config()
    attention, newcomer, ready = build_queues(cache["items"], config, cache["repo"])
    print("Maintainer queues for " + cache["repo"] + " (priority labels: "
          + str(config["priority_labels"]) + ")")
    print_queue("Needs attention", attention)
    print_queue("Newcomer support", newcomer)
    print_queue("Ready for review", ready)
    check_one_queue([attention, newcomer, ready])


if __name__ == "__main__":
    main()
