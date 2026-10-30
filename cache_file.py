# cache_file.py - Saving, loading and summarising the cache files.
# Each repo gets its own file, like cache_fastapi__fastapi.json.
# Called with no repo, the functions use DEFAULT_REPO, so older scripts keep working.

import json
import os

DEFAULT_REPO = "fastapi/fastapi"
OLD_CACHE_FILE = "cache.json"  # the single file used before each repo had its own


# Builds the cache file name for a repo. In: "fastapi/fastapi".
# Out: "cache_fastapi__fastapi.json" (two underscores, because a file name can't contain "/").
# GitHub ignores capitals in repo names, so we use small letters: "FastAPI/FastAPI" gets
# the same file, instead of a second copy of the same data.
def cache_path(repo):
    parts = repo.lower().split("/")
    return "cache_" + parts[0] + "__" + parts[1] + ".json"


# Finds the file to read for a repo: its own cache file, or the old cache.json
# for the default repo if the new file doesn't exist yet. In: repo. Out: file name, or None.
def find_cache_file(repo):
    if os.path.exists(cache_path(repo)):
        return cache_path(repo)
    if repo.lower() == DEFAULT_REPO and os.path.exists(OLD_CACHE_FILE):
        return OLD_CACHE_FILE
    return None


# Checks whether we have saved data for a repo. In: repo (optional). Out: True or False.
def cache_exists(repo=DEFAULT_REPO):
    return find_cache_file(repo) is not None


# Reads a repo's saved data. In: repo (optional). Out: the saved data as a dictionary.
def load_cache(repo=DEFAULT_REPO):
    with open(find_cache_file(repo)) as file:
        return json.load(file)


# Writes data to the repo's own cache file, nicely indented. In: dictionary. Out: nothing.
def save_cache(cache):
    path = cache_path(cache["repo"])
    with open(path, "w") as file:
        json.dump(cache, file, indent=2)
    print("Saved to " + path)


# Lists every repo that has saved data, by reading the cache file names.
# In: nothing. Out: list like ["fastapi/fastapi", "pallets/flask"].
def list_cached_repos():
    repos = []
    for name in sorted(os.listdir(".")):
        if name.startswith("cache_") and name.endswith(".json"):
            middle = name[len("cache_"):-len(".json")]
            owner, separator, repo_name = middle.partition("__")
            if separator == "__":
                repos.append(owner + "/" + repo_name)
    if DEFAULT_REPO not in repos and os.path.exists(OLD_CACHE_FILE):
        repos.append(DEFAULT_REPO)
    return repos


# Checks if a human other than the author commented or reviewed (bots don't count).
# In: one item. Out: True or False.
def has_reply(item):
    for person in item["comments"] + item["reviews"]:
        if person["login"] != item["author"] and person["user_type"] != "Bot":
            return True
    return False


# Prints the totals. In: the cache dictionary. Out: nothing.
def print_summary(cache):
    items = cache["items"]
    pr_count = 0
    reply_count = 0
    for item in items:
        if item["is_pr"]:
            pr_count = pr_count + 1
        if has_reply(item):
            reply_count = reply_count + 1
    print("")
    print("Summary for " + cache["repo"])
    print("  Total items: " + str(len(items)))
    print("  Issues: " + str(len(items) - pr_count))
    print("  PRs: " + str(pr_count))
    print("  With a reply from a human other than the author: " + str(reply_count))
    if not cache["complete"]:
        print("  Note: the fetch stopped early, so this data is incomplete.")
    print_label_counts(items)


# Counts how many items have each label, so the team can pick priority labels
# from real data. In: items. Out: nothing (it prints). Old caches have no labels.
def print_label_counts(items):
    counts = {}
    for item in items:
        for name in item.get("labels", []):
            counts[name] = counts.get(name, 0) + 1
    print("")
    if len(counts) == 0:
        print("Labels: none found (if this is old data, run python3 fetch.py owner/repo --refresh)")
        return
    print("Labels found (A to Z):")
    for name in sorted(counts):
        print("  " + name + ": " + str(counts[name]))
