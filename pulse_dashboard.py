# pulse_dashboard.py - Nishanth's Community Pulse dashboard, built with Streamlit.
# Run with: streamlit run pulse_dashboard.py
# It reads the saved cache files. The only network calls are the optional "Add a repo" box
# and the "Gemma notes" tab (GitHub reads plus Gemma on this computer).
# This file lays out the page; the tabs are in pulse_tabs.py, pulse_health.py and pulse_gemma.py.

import streamlit as st

from cache_file import DEFAULT_REPO, list_cached_repos, load_cache
from pulse_data import filter_rows, health_label, summary, waiting_rows
from pulse_gemma import gemma_tab
from pulse_health import health_tab
from pulse_parts import hero, load_css
from pulse_sidebar import brand, fetch_box, filters, mini_card, repo_picker
from pulse_tabs import contributors_tab, digest_tab, overview_tab, queues_tab, waiting_tab


# Picks which repo to show: one just added in the sidebar, the one picked before, or the default.
# In: list of repos with saved data. Out: nothing (it sets st.session_state["repo"]).
def choose_repo(repos):
    if st.session_state.get("pending_repo") in repos:  # a repo just added in the sidebar
        st.session_state["repo"] = st.session_state.pop("pending_repo")
    if st.session_state.get("repo") not in repos:
        if DEFAULT_REPO in repos:
            st.session_state["repo"] = DEFAULT_REPO
        else:
            st.session_state["repo"] = repos[0]


# Counts the waiting rows written by newcomers. In: rows. Out: a number.
def newcomer_count(rows):
    count = 0
    for row in rows:
        if row["newcomer"]:
            count = count + 1
    return count


# Builds the whole page: sidebar, banner and the seven tabs.
def main():
    st.set_page_config(page_title="Community Pulse", page_icon="💜", layout="wide")
    load_css()
    brand()
    repos = list_cached_repos()
    if len(repos) == 0:
        st.title("Community Pulse")
        st.info("No data yet. Run python3 fetch.py owner/repo, or use “Add a repo” in the sidebar.")
        fetch_box()
        return
    choose_repo(repos)
    repo = repo_picker(repos)
    items = load_cache(repo)["items"]
    numbers = summary(items)
    word, status = health_label(numbers["score"])
    all_rows = waiting_rows(items, repo)
    mini_card(numbers["score"], word, status, len(all_rows), newcomer_count(all_rows))
    fetch_box()
    newcomers_only, kinds, min_days, search = filters()
    hero(repo, numbers["dates"], numbers["score"], word, status)
    st.write("")
    rows = filter_rows(all_rows, newcomers_only, kinds or [], min_days, search)
    tabs = st.tabs(["Overview", "Health score", "Waiting (" + str(len(rows)) + ")", "Maintainer queues",
                    "Contributors", "Weekly digest", "Gemma notes"])
    with tabs[0]:
        overview_tab(numbers, items)
    with tabs[1]:
        health_tab(items, numbers, repo)
    with tabs[2]:
        waiting_tab(rows)
    with tabs[3]:
        queues_tab(items, repo)
    with tabs[4]:
        contributors_tab(numbers)
    with tabs[5]:
        digest_tab(items, repo)
    with tabs[6]:
        gemma_tab(items, repo)


main()
