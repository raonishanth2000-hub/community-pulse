# pulse_data.py - Prepares the numbers and table rows that pulse_dashboard.py shows.
# Plain Python, no Streamlit: it reuses the functions in metrics.py, health.py and
# priority_helpers.py, so the dashboard always agrees with the command-line tools.

from data_overview import date_range
from health import health_parts, health_score
from metric_helpers import first_reply_time, human_authored
from metrics import (NEWCOMER_TYPES, contributor_funnel, first_response_hours, median_first_response,
                     median_review_wait, newcomer_retention, still_waiting_list)
from priority_helpers import AUTHOR_WORDS

# Groups for the response-time chart, in the order they should appear.
RESPONSE_GROUPS = ["Under 1 h", "1-6 h", "6-24 h", "1-7 days", "Over 7 days"]


# Collects every headline number in one dictionary. In: items. Out: dictionary.
def summary(items):
    return {"first": median_first_response(items), "review": median_review_wait(items),
            "retention": newcomer_retention(items), "funnel": contributor_funnel(items),
            "score": health_score(items), "parts": health_parts(items), "dates": date_range(items)}


# Turns a score into a word and a status colour name. In: 0-100. Out: (word, colour name).
def health_label(score):
    if score >= 80:
        return "Healthy", "good"
    if score >= 50:
        return "Needs care", "warning"
    return "At risk", "critical"


# Builds one row per open item still waiting for a human reply or review.
# In: items and repo. Out: list of dictionaries, longest wait first.
def waiting_rows(items, repo):
    items_by_number = {}
    for item in items:
        items_by_number[item["number"]] = item
    rows = []
    for entry in still_waiting_list(items):
        item = items_by_number[entry["number"]]
        kind = "Issue"
        waiting_for = "First reply"
        if item["is_pr"]:
            kind = "PR"
        if first_reply_time(item) is not None:
            waiting_for = "Review"
        rows.append({"number": item["number"], "title": item["title"], "author": item["author"],
                     "who": AUTHOR_WORDS.get(item["author_association"], "contributor"),
                     "newcomer": item["author_association"] in NEWCOMER_TYPES, "type": kind,
                     "waiting for": waiting_for, "days": round(entry["age_hours"] / 24, 1),
                     "link": "https://github.com/" + repo + "/issues/" + str(item["number"])})
    return rows


# Keeps only the rows that match the filters chosen in the sidebar.
# In: rows, newcomers_only (True/False), kinds (list like ["PR"]), min_days, search text.
# Out: the matching rows.
def filter_rows(rows, newcomers_only, kinds, min_days, search):
    kept = []
    for row in rows:
        if newcomers_only and not row["newcomer"]:
            continue
        if row["type"] not in kinds or row["days"] < min_days:
            continue
        text = (row["title"] + " " + row["author"]).lower()
        if search.strip() != "" and search.strip().lower() not in text:
            continue
        kept.append(row)
    return kept


# Puts a first-response time into a group. In: hours. Out: a name from RESPONSE_GROUPS.
def response_group(hours):
    if hours < 1:
        return RESPONSE_GROUPS[0]
    if hours < 6:
        return RESPONSE_GROUPS[1]
    if hours < 24:
        return RESPONSE_GROUPS[2]
    if hours < 168:
        return RESPONSE_GROUPS[3]
    return RESPONSE_GROUPS[4]


# Counts how many human-opened items got their first human reply in each time group.
# In: items. Out: list of rows like {"group": "Under 1 h", "items": 12, "order": 0}.
def response_rows(items):
    counts = {}
    for name in RESPONSE_GROUPS:
        counts[name] = 0
    for item in human_authored(items):
        hours = first_response_hours(item)
        if hours is not None:
            counts[response_group(hours)] = counts[response_group(hours)] + 1
    rows = []
    for position in range(len(RESPONSE_GROUPS)):
        name = RESPONSE_GROUPS[position]
        rows.append({"group": name, "items": counts[name], "order": position})
    return rows


# Turns the funnel numbers into chart rows, in funnel order. In: funnel dictionary. Out: rows.
def funnel_rows(funnel):
    return [{"stage": "Opened an issue", "people": funnel["opened_issue"], "order": 0},
            {"stage": "Opened a PR", "people": funnel["opened_pr"], "order": 1},
            {"stage": "Came back", "people": funnel["repeat"], "order": 2}]
