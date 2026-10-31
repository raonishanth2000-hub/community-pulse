# pulse_health.py - The "Health score" tab of pulse_dashboard.py.
# Left: each part of the score, with a "How is this worked out?" button showing the real
# numbers and the rule. Right: a "What if?" panel where sliders change the inputs and the
# score updates straight away. It uses the same rules as health.py, so the maths always matches.

import streamlit as st

from health import (NEWCOMER_POINTS, NEWCOMER_WAIT_HOURS, RESPONSE_FULL_HOURS, RESPONSE_POINTS,
                    RESPONSE_ZERO_HOURS, REVIEW_FULL_HOURS, REVIEW_POINTS, REVIEW_ZERO_HOURS,
                    UNANSWERED_POINTS)
from health_helpers import newcomer_long_wait_share, share_points, sliding_points, unanswered_share
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


# Picks a slider's starting value: the real number, or a stand-in if there's no data.
# In: real value or None, stand-in, largest slider value. Out: a whole number.
def start_value(value, stand_in, largest):
    if value is None:
        return stand_in
    return min(largest, round(value))


# Works out the score from the four slider numbers, with the same rules as health.py.
# In: hours, hours, percent, percent. Out: score.
def slider_score(first, review, stuck, unanswered):
    return (sliding_points(first, RESPONSE_FULL_HOURS, RESPONSE_ZERO_HOURS, RESPONSE_POINTS)
            + sliding_points(review, REVIEW_FULL_HOURS, REVIEW_ZERO_HOURS, REVIEW_POINTS)
            + share_points(stuck / 100, NEWCOMER_POINTS) + share_points(unanswered / 100, UNANSWERED_POINTS))


# The right column: four sliders, and the score those numbers would give.
# The sliders start at today's numbers (rounded to whole numbers), so we show today's real
# score plus the CHANGE the sliders make; untouched sliders always show exactly today's score.
# In: inputs, the real score, repo name (so each repo keeps its own sliders). Out: nothing.
def what_if_column(inputs, real_score, repo):
    st.subheader("What if?")
    st.caption("Move a slider to see how the score would change. Nothing is saved.")
    starts = [start_value(inputs["first"], RESPONSE_FULL_HOURS, 200),
              start_value(inputs["review"], REVIEW_FULL_HOURS, 400),
              start_value(percent_number(inputs["stuck"]), 0, 100),
              start_value(percent_number(inputs["unanswered"]), 0, 100)]
    first = st.slider("Median first reply (hours)", 0, 200, starts[0], key="first " + repo)
    review = st.slider("Median PR review wait (hours)", 0, 400, starts[1], key="review " + repo)
    stuck = st.slider("Newcomer items stuck over 7 days (%)", 0, 100, starts[2], key="stuck " + repo)
    unanswered = st.slider("Open items nobody has answered (%)", 0, 100, starts[3], key="unanswered " + repo)
    change = slider_score(first, review, stuck, unanswered) - slider_score(starts[0], starts[1], starts[2], starts[3])
    new_score = max(0, min(100, real_score + change))
    colour = "normal"  # green when the score goes up, red when it goes down
    if round(new_score - real_score, 1) == 0:
        colour = "off"  # grey: nothing has changed yet
    st.metric("Score with these numbers", str(round(new_score, 1)) + " / 100",
              delta=str(round(new_score - real_score, 1)) + " compared with now", delta_color=colour)


# Turns a share (0 to 1) into a percentage number, keeping None as None. In: share. Out: number.
def percent_number(share):
    if share is None:
        return None
    return share * 100


# The whole tab: parts on the left, "What if?" on the right. In: items, summary, repo. Out: nothing.
def health_tab(items, numbers, repo):
    inputs = score_inputs(items, numbers)
    left, right = st.columns(2, gap="large")
    with left:
        parts_column(inputs, numbers["parts"])
    with right:
        what_if_column(inputs, numbers["score"], repo)
