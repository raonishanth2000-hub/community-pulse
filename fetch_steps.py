# fetch_steps.py - The download steps used by fetch_repo in fetch.py.
# Gets the list of issues and PRs, then the comments and reviews of each one.
# Every GitHub call goes through get_json, which raises a plain-English error if it fails.

from github_api import get_json
from simplify import describe_user, simplify_item

MAX_ITEMS = 300
PAGES = 3
LOW_RATE_LIMIT = 20  # stop when GitHub says fewer calls than this are left


# Passes a progress update on to whoever asked for them (if anyone did).
# In: the progress function or None, steps done, total steps, message. Out: nothing.
def tell(progress, done, total, message):
    if progress is not None:
        progress(done, total, message)


# Gets the newest issues and PRs, up to 3 pages of 100.
# In: repo, token, progress function. Out: list of raw items, and calls left.
def fetch_item_list(repo, token, progress):
    items = []
    calls_left = 5000
    for page in range(1, PAGES + 1):
        path = "/repos/" + repo + "/issues?state=all&per_page=100&page=" + str(page)
        data, calls_left = get_json(path + "&sort=created&direction=desc", token)
        items.extend(data)
        tell(progress, page, PAGES, "Fetched page " + str(page) + " of " + str(PAGES))
        if len(data) < 100 or len(items) >= MAX_ITEMS:
            break
    return items[:MAX_ITEMS], calls_left


# Fetches the comments (and reviews, for PRs) of one item.
# In: repo, token, raw item, calls left. Out: simplified item and calls left.
def fetch_replies(repo, token, raw, calls_left):
    item = simplify_item(raw)
    number = str(item["number"])
    if raw["comments"] > 0:
        data, calls_left = get_json("/repos/" + repo + "/issues/" + number + "/comments?per_page=100", token)
        for comment in data:
            login, user_type = describe_user(comment["user"])
            item["comments"].append({"login": login, "user_type": user_type,
                                     "created_at": comment["created_at"]})
    if item["is_pr"]:
        data, calls_left = get_json("/repos/" + repo + "/pulls/" + number + "/reviews?per_page=100", token)
        for review in data:
            login, user_type = describe_user(review["user"])
            item["reviews"].append({"login": login, "user_type": user_type,
                                    "state": review["state"], "submitted_at": review.get("submitted_at")})
    return item, calls_left


# Fetches replies for every item, stopping early if the rate limit runs low or GitHub fails.
# In: repo, token, raw items, calls left, progress function.
# Out: the finished items, and a problem message (None if everything worked).
def fetch_all_replies(repo, token, raw_items, calls_left, progress):
    items = []
    for raw in raw_items:
        if calls_left < LOW_RATE_LIMIT:
            return items, "GitHub rate limit almost used up, so we stopped early"
        try:
            item, calls_left = fetch_replies(repo, token, raw, calls_left)
        except RuntimeError as error:
            return items, str(error)
        items.append(item)
        tell(progress, len(items), len(raw_items),
             "Fetched replies for " + str(len(items)) + " of " + str(len(raw_items)))
    return items, None
