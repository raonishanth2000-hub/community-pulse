# pulse_gemma.py - The "Gemma notes" tab of pulse_dashboard.py.
# It runs the Stage 8 check (priority_info.py) from a button: Gemma, a local AI model running
# through Ollama, turns the repo's CONTRIBUTING file into yes/no checks and checks waiting PRs.
# It only works on a computer running Ollama; the hosted app shows how to try it instead.
# The Code of Conduct is never sent to the model, and nothing is ever posted to GitHub.

import html

import requests
import streamlit as st

from guidelines import load_saved_checklist
from local_model import MODEL
from priority_helpers import load_config
from priority_info import build_priority_info
from priority_notes import priority_then_wait, waiting_items
from pulse_parts import card, show

OLLAMA_TAGS_URL = "http://localhost:11434/api/tags"


# Checks whether Ollama is running here with the Gemma model installed.
# In: nothing. Out: True or False. Waits at most 2 seconds.
def model_is_running():
    try:
        response = requests.get(OLLAMA_TAGS_URL, timeout=2)
        models = response.json().get("models") or []
    except (requests.RequestException, ValueError):
        return False
    for model in models:
        if model.get("name") == MODEL:
            return True
    return False


# Shown when Gemma can't be reached (for example on the hosted app). In: nothing. Out: nothing.
def not_running_message():
    st.info("Gemma runs on your own computer through Ollama, so it isn't available here. "
            "To try it, run the dashboard on a computer with Ollama and " + MODEL + " installed:")
    st.code("ollama pull " + MODEL + "\nstreamlit run pulse_dashboard.py", language="bash")


# Picks a card colour for one item: teal = meets every check, amber = something missing,
# violet = no guideline check (labels or nothing). In: the item's info. Out: colour name.
def accent_for(details):
    if details["source"] != "guidelines":
        return "violet"
    if details["is_priority"]:
        return "teal"
    return "amber"


# One waiting item with Gemma's note. In: repo, item, days waiting, its info. Out: nothing.
# GitHub sends /issues/ links on to /pull/ for PRs, so one link works for both.
def note_card(repo, item, days, details):
    kind = "Issue"
    if item["is_pr"]:
        kind = "PR"
    note = details["note"] or "No guideline check or priority label"
    url = "https://github.com/" + repo + "/issues/" + str(item["number"])
    show('<div class="pulse-item" style="--accent:var(--' + accent_for(details) + ')">'
         '<a href="' + html.escape(url) + '" target="_blank">#' + str(item["number"]) + " "
         + html.escape(item["title"]) + "</a>"
         '<div class="pulse-item-meta">' + kind + " · " + str(days) + " days waiting · from "
         + html.escape(details["source"]) + " · " + html.escape(note) + "</div>"
         '<div class="pulse-item-action">→ ' + html.escape(details["next_action"]) + "</div></div>")


# Counts how many items got their note from each source. In: info dictionary. Out: dictionary.
def source_counts(info):
    counts = {"guidelines": 0, "labels": 0, "none": 0}
    for details in info.values():
        counts[details["source"]] = counts[details["source"]] + 1
    return counts


# Shows the results: three count cards, the checklist, then every waiting item.
# In: items, repo and the info dictionary from build_priority_info. Out: nothing.
def show_results(items, repo, info):
    counts = source_counts(info)
    col1, col2, col3 = st.columns(3)
    with col1:
        card("Checked by Gemma", str(counts["guidelines"]), "PRs checked against the guidelines", "teal")
    with col2:
        card("Priority labels", str(counts["labels"]), "fell back to GitHub labels", "violet")
    with col3:
        card("No note", str(counts["none"]), "no checks and no priority label", "violet-soft")
    checklist = load_saved_checklist(repo)
    if checklist:
        st.subheader("Checks made from CONTRIBUTING")
        for check in checklist:
            st.markdown("- " + check)
    else:
        st.warning("No checks for this repo: its CONTRIBUTING file is missing or too short (it may just "
                   "link to another page), so Gemma had nothing to check PRs against. Notes below come "
                   "from priority labels instead. You can write checklist.json by hand.")
    st.subheader("Waiting items, priority first")
    rows = []
    for item, days in waiting_items(items):
        if item["number"] in info:
            rows.append((item, days, info[item["number"]]))
    rows.sort(key=priority_then_wait, reverse=True)
    for item, days, details in rows:
        note_card(repo, item, days, details)


# The whole tab. In: items and repo. Out: nothing. Results are kept per repo until the page reloads.
def gemma_tab(items, repo):
    st.caption("Gemma (" + MODEL + ") reads the repo's CONTRIBUTING file and checks up to 10 waiting PRs. "
               "It runs only on this computer; the Code of Conduct is never sent to it.")
    if not model_is_running():
        not_running_message()
        return
    key = "gemma " + repo
    if st.button("Run Gemma on waiting PRs", type="primary"):
        with st.spinner("Gemma is reading the guidelines and checking PRs. This takes a minute or two..."):
            st.session_state[key] = build_priority_info(repo, items, load_config())
    if key not in st.session_state:
        st.write("Click the button to start. Nothing is sent to the internet except GitHub reads.")
        return
    show_results(items, repo, st.session_state[key])
