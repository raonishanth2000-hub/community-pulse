# pulse_sidebar.py - The sidebar of pulse_dashboard.py: the brand, a mini health card,
# the "Add a repo" box, and the filters for the waiting list (with "Clear filters").

import streamlit as st

from fetch import fetch_repo, is_valid_repo
from pulse_parts import chip

# Every filter's starting value. Each widget is linked to st.session_state by this key,
# so "Clear filters" can put them all back by setting these values again.
FILTER_DEFAULTS = {"f_newcomers": False, "f_kinds": ["Issue", "PR"], "f_min_days": 0, "f_search": ""}


# Shows HTML in the sidebar (not the main page). In: HTML text. Out: nothing.
def side(html_text):
    st.sidebar.markdown(html_text, unsafe_allow_html=True)


# The name at the top of the sidebar, with a small dot that beats like a pulse.
def brand():
    side('<div class="pulse-brand"><span class="pulse-dot"></span>Community Pulse</div>')


# A small grey section title in capitals, with an optional badge on the right.
# In: title and badge HTML ("" for none). Out: nothing.
def section(title, badge):
    side('<div class="pulse-section"><span>' + title + "</span>" + badge + "</div>")


# A thin line between sidebar sections. In/Out: nothing.
def divider():
    side('<div class="pulse-divider"></div>')


# The REPOSITORY section's dropdown. The section title already says what it is, so the
# dropdown's own label is hidden. In: list of repos. Out: the picked repo.
def repo_picker(repos):
    section("Repository", "")
    return st.sidebar.selectbox("Repository", repos, key="repo", label_visibility="collapsed")


# A small card under the repo picker: score, status, and how many people are waiting.
# In: score, status word, status name, waiting count, newcomers waiting. Out: nothing.
def mini_card(score, word, status, waiting, newcomers_waiting):
    side('<div class="pulse-side-card"><div class="pulse-side-top">'
         '<span class="pulse-side-score">' + str(round(score)) + "<small>/100</small></span>"
         + chip(word, status) + '</div><div class="pulse-bar"><div style="width:' + str(round(score))
         + '%"></div></div><div class="pulse-side-note">' + str(waiting) + " waiting · "
         + str(newcomers_waiting) + " of them newcomers</div></div>")


# Sidebar box to download a new repo, with a live progress bar. In/Out: nothing.
def fetch_box():
    with st.sidebar.expander("Add a repo", icon=":material/add:"):
        new_repo = st.text_input("owner/name", placeholder="pallets/flask")
        if st.button("Fetch it", width="stretch"):
            if not is_valid_repo(new_repo):
                st.error("Use owner/name, like pallets/flask.")
                return
            bar = st.progress(0.0, text="Starting...")

            # fetch_repo calls this after every step, so the bar moves while it works.
            def show_progress(done, total, message):
                bar.progress(min(done / total, 1.0), text=message)

            try:
                fetch_repo(new_repo, show_progress)
            except (RuntimeError, ValueError) as error:
                st.error(str(error))
                return
            # The repo dropdown is already on the page, so we can't change it here. We leave a
            # note instead; main() picks it up on the next run, before drawing the dropdown.
            st.session_state["pending_repo"] = new_repo.lower()
            st.rerun()


# Puts every filter back to its starting value. Streamlit runs this when "Clear filters"
# is clicked, before the page is drawn again. In/Out: nothing.
def clear_filters():
    for key in FILTER_DEFAULTS:
        st.session_state[key] = FILTER_DEFAULTS[key]


# Counts how many filters are different from their starting value. In: nothing. Out: number.
def active_filter_count():
    count = 0
    for key in FILTER_DEFAULTS:
        value = st.session_state.get(key)
        default = FILTER_DEFAULTS[key]
        if isinstance(default, list):  # the order of picked types doesn't matter
            value = sorted(value or [])
            default = sorted(default)
        if value != default:
            count = count + 1
    return count


# Sidebar filters for the waiting list. In: nothing. Out: the four filter values.
def filters():
    for key in FILTER_DEFAULTS:
        if key not in st.session_state:
            st.session_state[key] = FILTER_DEFAULTS[key]
    count = active_filter_count()
    badge = ""
    if count > 0:
        badge = '<span class="pulse-count">' + str(count) + " on</span>"
    divider()
    section("Filter waiting list", badge)
    search = st.sidebar.text_input("Search", placeholder="Search title or author", key="f_search",
                                   label_visibility="collapsed", icon=":material/search:")
    newcomers_only = st.sidebar.toggle("Newcomers only", key="f_newcomers")
    kinds = st.sidebar.pills("Type", ["Issue", "PR"], selection_mode="multi", key="f_kinds")
    min_days = st.sidebar.slider("Waiting at least (days)", 0, 60, key="f_min_days")
    st.sidebar.button("Clear filters", on_click=clear_filters, disabled=count == 0, width="stretch",
                      icon=":material/filter_alt_off:")
    return newcomers_only, kinds, min_days, search
