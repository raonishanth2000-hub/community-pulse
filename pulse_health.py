# pulse_health.py - The "Health score" tab of pulse_dashboard.py.
# Left: each part of the score, with a "How is this worked out?" button showing the real
# numbers and the rule. Right: how the four parts add up to the total. The numbers come from
# health.py, so the dashboard and the command line always match.

import streamlit as st

from health import (NEWCOMER_POINTS, NEWCOMER_WAIT_HOURS, RESPONSE_FULL_HOURS, RESPONSE_POINTS,
                    RESPONSE_ZERO_HOURS, REVIEW_FULL_HOURS, REVIEW_POINTS, REVIEW_ZERO_HOURS,
                    UNANSWERED_POINTS)
from health_helpers import newcomer_long_wait_share, unanswered_share
from pulse_parts import health_bar


# Shows a share (0 to 1) as a whole percentage, or "no data". In: share or None. Out: text.
def percent_text(share):
    if share is None:
        return "no data"
    return str(round(share * 100)) + "%"


# Shows hours as text, or "no data". In: hours or None. Out: text.
def hours_text(hours):
    if hours is None:
        return "no data"
    return str(round(hours, 1)) + " h"


# Collects the four numbers the score is built from. In: items and the dashboard summary.
# Out: dictionary with first, review (hours) and stuck, unanswered (shares from 0 to 1).
def score_inputs(items, numbers):
    return {"first": numbers["first"]["median_hours"], "review": numbers["review"]["median_hours"],
            "stuck": newcomer_long_wait_share(items, NEWCOMER_WAIT_HOURS),
            "unanswered": unanswered_share(items)}


# One part of the score: its bar, then a button that opens the explanation.
# In: name, points, most points, explanation text. Out: nothing.
def part_row(name, points, max_points, explanation):
    health_bar(name, points, max_points)
    with st.popover("How is this worked out?"):
        st.markdown(explanation + "\n\nNo data for this part gives **half marks**.")


# The left column: all four parts with their explanations. In: inputs and parts. Out: nothing.
def parts_column(inputs, parts):
    st.subheader("The four parts")
    part_row("Fast first reply", parts["response"], RESPONSE_POINTS,
             "Median wait for a first human reply: **" + hours_text(inputs["first"]) + "**.  \nFull "
             + str(RESPONSE_POINTS) + " points at " + str(RESPONSE_FULL_HOURS) + " h or less, 0 points at "
             + str(RESPONSE_ZERO_HOURS) + " h or more, a straight line in between.")
    part_row("Fast PR review", parts["review"], REVIEW_POINTS,
             "Median wait for a first human PR review: **" + hours_text(inputs["review"]) + "**.  \nFull "
             + str(REVIEW_POINTS) + " points at " + str(REVIEW_FULL_HOURS) + " h or less, 0 points at "
             + str(REVIEW_ZERO_HOURS) + " h or more.")
    part_row("Newcomers not left waiting", parts["newcomer"], NEWCOMER_POINTS,
             "Newcomer items stuck for over 7 days: **" + percent_text(inputs["stuck"]) + "**.  \nPoints = "
             + str(NEWCOMER_POINTS) + " × (1 − that share).")
    part_row("Few unanswered open items", parts["unanswered"], UNANSWERED_POINTS,
             "Open items with no human reply or review at all: **" + percent_text(inputs["unanswered"])
             + "**.  \nPoints = " + str(UNANSWERED_POINTS) + " × (1 − that share).")


# The right column: the total, and how the parts add up to it. In: score and parts. Out: nothing.
def total_column(score, parts):
    st.subheader("How it adds up")
    st.metric("Health score", str(round(score, 1)) + " / 100")
    st.markdown("Fast first reply **" + str(round(parts["response"], 1)) + "** + fast PR review **"
                + str(round(parts["review"], 1)) + "** + newcomers not left waiting **"
                + str(round(parts["newcomer"], 1)) + "** + few unanswered items **"
                + str(round(parts["unanswered"], 1)) + "**.")
    st.markdown("**80 or more** is Healthy, **50 to 79** Needs care, and **under 50** At risk.")


# The whole tab: parts on the left, the total on the right. In: items and summary. Out: nothing.
def health_tab(items, numbers):
    inputs = score_inputs(items, numbers)
    left, right = st.columns(2, gap="large")
    with left:
        parts_column(inputs, numbers["parts"])
    with right:
        total_column(numbers["score"], numbers["parts"])
