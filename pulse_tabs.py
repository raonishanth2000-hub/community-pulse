# pulse_tabs.py - What goes inside the Overview, Waiting, Maintainer queues and
# Contributors tabs of pulse_dashboard.py. (The Health score tab is in pulse_health.py.)

import streamlit as st

from health import NEWCOMER_POINTS, RESPONSE_POINTS, REVIEW_POINTS, UNANSWERED_POINTS
from priority import build_queues
from priority_helpers import load_config
from pulse_charts import funnel_chart, response_chart
from pulse_data import funnel_rows, response_rows
from pulse_parts import card, health_bar, queue_column


# Shows hours as short text: "5.6 h", "3.2 days" for long waits, or "n/a". In: hours or None.
def hours_text(hours):
    if hours is None:
        return "n/a"
    if hours >= 48:
        return str(round(hours / 24, 1)) + " days"
    return str(round(hours, 1)) + " h"


# The Overview tab: four number cards, the health score parts and the response chart.
def overview_tab(numbers, items):
    retention = numbers["retention"]
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        card("Median first response", hours_text(numbers["first"]["median_hours"]),
             str(numbers["first"]["counted"]) + " items got a human reply", "violet")
    with col2:
        card("Median PR review wait", hours_text(numbers["review"]["median_hours"]),
             "based on " + str(numbers["review"]["counted"]) + " PRs", "amber")
    with col3:
        card("Newcomer retention", str(retention["percent"] or 0) + "%",
             str(retention["came_back"]) + " of " + str(retention["newcomers"]) + " came back in 30 days", "teal")
    with col4:
        card("Repeat contributors", str(numbers["funnel"]["repeat"]), "opened 2 or more items", "violet-soft")
    st.write("")
    left, right = st.columns([2, 3], gap="large")
    with left:
        st.subheader("What makes the score")
        parts = numbers["parts"]
        health_bar("Fast first reply", parts["response"], RESPONSE_POINTS)
        health_bar("Fast PR review", parts["review"], REVIEW_POINTS)
        health_bar("Newcomers not left waiting", parts["newcomer"], NEWCOMER_POINTS)
        health_bar("Few unanswered open items", parts["unanswered"], UNANSWERED_POINTS)
    with right:
        st.subheader("How fast people hear back")
        st.altair_chart(response_chart(response_rows(items)), width="stretch")


# The Waiting tab: a filtered, sortable table of everyone still waiting.
def waiting_tab(rows):
    st.caption(str(len(rows)) + " open items still waiting for a human reply or review. "
               "Click a column to sort; use the sidebar to filter.")
    if len(rows) == 0:
        st.success("Nobody matching these filters is waiting.")
        return
    longest = max(1.0, rows[0]["days"])
    st.dataframe(rows, hide_index=True, width="stretch",
                 column_order=["number", "title", "link", "days", "waiting for", "who", "type"],
                 column_config={
        "days": st.column_config.ProgressColumn("Days waiting", min_value=0, max_value=longest, format="%.1f"),
        "newcomer": st.column_config.CheckboxColumn("Newcomer"),
        "link": st.column_config.LinkColumn("Link", display_text="Open ↗")})


# The Maintainer queues tab: the three queues from priority.py, side by side.
def queues_tab(items, repo):
    attention, newcomer, ready = build_queues(items, load_config(), repo)
    col1, col2, col3 = st.columns(3, gap="medium")
    with col1:
        queue_column("Newcomer support", newcomer, "teal", 6)
    with col2:
        queue_column("Ready for review", ready, "violet", 6)
    with col3:
        queue_column("Needs attention", attention, "amber", 6)


# The Contributors tab: the funnel chart, with the newcomer count beside it.
def contributors_tab(numbers):
    left, right = st.columns([3, 1], gap="large")
    with left:
        st.subheader("Contributor funnel")
        st.caption("Different people at each stage, from the latest items. “Came back” means they "
                   "opened 2 or more issues or PRs. Bots are left out.")
        st.altair_chart(funnel_chart(funnel_rows(numbers["funnel"])), width="stretch")
    with right:
        card("Newcomers", str(numbers["retention"]["newcomers"]), "first-time or outside authors", "teal")
