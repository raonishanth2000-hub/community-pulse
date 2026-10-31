# priority_notes.py - The small pieces behind priority_info.py: which items are waiting,
# and the note and next action for each one, from the guideline answers or from labels.

from metrics import still_waiting_list
from priority_helpers import priority_labels_found


# 1. Finds the item's priority labels (capitals don't matter; no labels field = no match).
# In: item and config. Out: list of matching label names (empty if none).
def label_priority(item, config):
    return priority_labels_found(item, config)


# Picks the open, human-opened, non-draft items still waiting for a reply or review,
# using still_waiting_list from metrics.py. In: items. Out: list of (item, days waiting), longest first.
def waiting_items(items):
    items_by_number = {}
    for item in items:
        items_by_number[item["number"]] = item
    waiting = []
    for entry in still_waiting_list(items):
        item = items_by_number[entry["number"]]
        if not item["draft"]:
            waiting.append((item, round(entry["age_hours"] / 24, 1)))
    return waiting


# Builds the note when the model answered the checks. In: checks and answers. Out: info dictionary.
def guideline_info(checklist, answers):
    met = 0
    missing = []
    unclear = []
    for position in range(len(checklist)):
        if answers[position] == "yes":
            met = met + 1
        elif answers[position] == "no":
            missing.append(checklist[position])
        else:
            unclear.append(checklist[position])
    note = "Meets " + str(met) + " of " + str(len(checklist)) + " guideline checks"
    if len(missing) > 0:
        note = note + "; missing: " + ", ".join(missing)
    if len(unclear) > 0:
        note = note + "; unclear: " + ", ".join(unclear)
    action = "Review this PR (meets the guidelines)"
    if len(missing) > 0:
        action = "Ask the author to add: " + ", ".join(missing)
    return {"source": "guidelines", "is_priority": len(missing) == 0, "note": note, "next_action": action}


# Builds the note without the model: priority labels if any match, otherwise nothing.
# In: item and config. Out: info dictionary.
def fallback_info(item, config):
    action = "Reply to the author"
    if item["is_pr"]:
        action = "Review this PR"
    found = label_priority(item, config)
    if len(found) > 0:
        return {"source": "labels", "is_priority": True,
                "note": "Priority label: " + ", ".join(found), "next_action": action}
    return {"source": "none", "is_priority": False, "note": "", "next_action": action}


# Used for sorting: priority items first, then the longest wait. In: (item, days, info). Out: a pair.
def priority_then_wait(row):
    return (row[2]["is_priority"], row[1])
