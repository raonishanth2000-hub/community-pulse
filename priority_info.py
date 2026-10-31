# priority_info.py - Stage 8: a priority note for every item still waiting, from the repo's
# CONTRIBUTING guidelines (checked by a local AI model), or from priority labels as a fallback.
# Usage: python3 priority_info.py [owner/repo]. It only reads; it never posts anything to GitHub.

import sys

from cache_file import DEFAULT_REPO, cache_exists, load_cache
from fetch import is_valid_repo
from guidelines import check_pr, find_guidelines, make_checklist, save_json
from priority_helpers import load_config
# label_priority isn't used in this file; it's imported so other code can get it from here too.
from priority_notes import (fallback_info, guideline_info, label_priority,
                            priority_then_wait, waiting_items)

INFO_FILE = "priority_info.json"
MAX_MODEL_CHECKS = 10  # only the 10 longest-waiting PRs go to the model, so the run stays short


# 2. Decides the priority info for every waiting item, and saves priority_info.json.
# In: repo, items, config. Out: dictionary keyed by item number.
def build_priority_info(repo, items, config):
    checklist = []
    text = find_guidelines(repo)
    if text is not None:
        checklist = make_checklist(text, repo)
    info = {}
    model_checks = 0
    model_working = len(checklist) > 0
    for item, days in waiting_items(items):
        answers = None
        if item["is_pr"] and model_working and model_checks < MAX_MODEL_CHECKS:
            model_checks = model_checks + 1
            print("Checking PR #" + str(item["number"]) + " against the guidelines ("
                  + str(model_checks) + " of up to " + str(MAX_MODEL_CHECKS) + ")...")
            answers = check_pr(item, checklist)
            if answers is None:
                model_working = False  # stop asking; every other item uses the fallback
        if answers is not None:
            info[item["number"]] = guideline_info(checklist, answers)
        else:
            info[item["number"]] = fallback_info(item, config)
    save_json(INFO_FILE, info)
    return info


# 4. Prints every waiting item (priority first, then longest wait) and a short summary.
# In: items and the info dictionary. Out: nothing (it prints).
def print_report(items, info):
    rows = []
    for item, days in waiting_items(items):
        rows.append((item, days, info[item["number"]]))
    rows.sort(key=priority_then_wait, reverse=True)
    counts = {"guidelines": 0, "labels": 0, "none": 0}
    print("")
    for item, days, details in rows:
        counts[details["source"]] = counts[details["source"]] + 1
        flag = ""
        if details["is_priority"]:
            flag = "  PRIORITY"
        print("#" + str(item["number"]) + ", " + str(days) + " days [" + details["source"] + "]" + flag)
        if details["note"] != "":
            print("    Note: " + details["note"])
        print("    Next: " + details["next_action"])
    print("")
    print("Summary: " + str(counts["guidelines"]) + " used guidelines, " + str(counts["labels"])
          + " used labels, " + str(counts["none"]) + " had neither. Saved to " + INFO_FILE)


# Reads the repo from the command line, builds the info, and prints it.
def main():
    repo = DEFAULT_REPO
    if len(sys.argv) > 1:
        repo = sys.argv[1]
    if not is_valid_repo(repo):
        print("'" + repo + "' is not a valid repo name. Use owner/name, like fastapi/fastapi.")
        sys.exit(1)
    repo = repo.lower()
    if not cache_exists(repo):
        print("No saved data for " + repo + " yet. Run python3 fetch.py " + repo + " first.")
        sys.exit(1)
    items = load_cache(repo)["items"]
    info = build_priority_info(repo, items, load_config())
    print_report(items, info)


if __name__ == "__main__":
    main()
