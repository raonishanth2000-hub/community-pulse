# fetch.py - Stage 1 of Community Pulse: downloads the latest 300 issues and PRs of any
# public repo, plus their comments and reviews, and saves them to that repo's cache file.
# Command line: python3 fetch.py [owner/repo] [--refresh]
# From other code: from fetch import fetch_repo, then items = fetch_repo("owner/repo")

import string
import sys
from datetime import datetime, timezone

from cache_file import DEFAULT_REPO, cache_exists, load_cache, print_summary, save_cache
from fetch_steps import fetch_all_replies, fetch_item_list, tell
from github_api import read_token

ALLOWED_CHARACTERS = string.ascii_letters + string.digits + ".-_"


# Reads the command line. In: nothing. Out: repo name, and True/False for --refresh.
def read_settings():
    repo = DEFAULT_REPO
    refresh = False
    for arg in sys.argv[1:]:
        if arg == "--refresh":
            refresh = True
        else:
            repo = arg
    return repo, refresh


# Checks a repo name is safe to use: exactly owner/name, using only letters,
# digits, dots, dashes and underscores. "." and ".." are refused because in
# paths and web addresses they mean "this folder" and "go up a folder".
# In: text. Out: True or False.
def is_valid_repo(text):
    parts = text.split("/")
    if len(parts) != 2:
        return False
    for part in parts:
        if part == "" or part == "." or part == "..":
            return False
        for character in part:
            if character not in ALLOWED_CHARACTERS:
                return False
    return True


# The whole fetch as one function other code can call. Uses saved data unless refresh is True.
# In: repo, optional progress function, optional refresh. Out: the list of items.
# Raises an error with a plain-English message if anything goes wrong; if it stops
# halfway, what we got so far is saved first.
def fetch_repo(repo, progress=None, refresh=False):
    if not is_valid_repo(repo):
        raise ValueError("'" + repo + "' is not a valid repo name. Use owner/name, like fastapi/fastapi.")
    repo = repo.lower()  # GitHub ignores capitals, so FastAPI/FastAPI and fastapi/fastapi are the same
    if cache_exists(repo) and not refresh:
        tell(progress, 1, 1, "Using saved data for " + repo + " (refresh to fetch again)")
        return load_cache(repo)["items"]
    token = read_token()
    raw_items, calls_left = fetch_item_list(repo, token, progress)
    if len(raw_items) == 0:
        raise RuntimeError("GitHub returned no issues or pull requests for " + repo
                           + ". It may have none yet, or have issues turned off.")
    items, problem = fetch_all_replies(repo, token, raw_items, calls_left, progress)
    save_cache({"repo": repo, "fetched_at": datetime.now(timezone.utc).isoformat(),
                "complete": problem is None, "items": items})
    if problem is not None:
        raise RuntimeError(problem + ". Saved the " + str(len(items)) + " items fetched so far.")
    return items


# Prints progress on the command line: every page, then every 25 items, so it doesn't flood.
# In: steps done, total steps, message. Out: nothing (it prints).
def print_progress(done, total, message):
    if "page" in message or done % 25 == 0 or done == total:
        print(message)


# Command line: fetch the repo, print plain-English errors, then print a summary.
def main():
    repo, refresh = read_settings()
    try:
        fetch_repo(repo, print_progress, refresh)
    except (RuntimeError, ValueError) as error:
        print("Error: " + str(error))
        sys.exit(1)
    print_summary(load_cache(repo))


if __name__ == "__main__":
    main()
