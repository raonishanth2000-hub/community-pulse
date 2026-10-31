# pulse_parts.py - Small pieces of the Pulse dashboard's page, built as HTML.
# Any text that comes from GitHub (titles, names) goes through html.escape first,
# so a PR title can't break or change the page.

import html
import os

import streamlit as st

CSS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pulse_style.css")
STATUS_COLOURS = {"good": "var(--good)", "warning": "var(--warning)", "critical": "var(--critical)"}
STATUS_ICONS = {"good": "●", "warning": "▲", "critical": "■"}


# Adds the dashboard's stylesheet to the page. In: nothing. Out: nothing.
def load_css():
    with open(CSS_FILE) as file:
        st.markdown("<style>" + file.read() + "</style>", unsafe_allow_html=True)


# Shows raw HTML on the page. In: HTML text. Out: nothing.
def show(html_text):
    st.markdown(html_text, unsafe_allow_html=True)


# Status chip: an icon and a word in the status colour (never colour alone).
# In: word and status name ("good", "warning", "critical"). Out: HTML text.
def chip(word, status):
    return ('<span class="pulse-chip" style="--chip:' + STATUS_COLOURS[status] + '">'
            + STATUS_ICONS[status] + " " + html.escape(word) + "</span>")


# The banner at the top: repo, dates, status chip and the health ring.
# In: repo, the date range dictionary, score, status word and status name. Out: nothing.
def hero(repo, dates, score, word, status):
    show('<div class="pulse-hero"><div>'
         '<div class="pulse-eyebrow">Community Pulse</div>'
         "<h1>" + html.escape(repo) + "</h1>"
         '<div class="pulse-sub">Latest issues and PRs from ' + dates["oldest"][:10] + " to "
         + dates["newest"][:10] + " (" + str(dates["days"]) + " days)</div>"
         '<div style="margin-top:12px">' + chip(word, status) + "</div></div>"
         '<div class="pulse-ring" style="--score:' + str(score) + ";--ring-color:" + STATUS_COLOURS[status] + '">'
         # The number is drawn by CSS (pulse_style.css) so it can count up from 0 to the score.
         '<div class="pulse-ring-inner"><div><div class="pulse-ring-score" style="--target:' + str(round(score))
         + '"></div><div class="pulse-ring-label">health / 100</div></div></div></div></div>')


# One number card. In: title, value text, small note, accent colour name. Out: nothing.
def card(title, value, note, accent):
    show('<div class="pulse-card" style="--accent:var(--' + accent + ')">'
         '<div class="pulse-card-title">' + html.escape(title) + "</div>"
         '<div class="pulse-card-value">' + html.escape(value) + "</div>"
         '<div class="pulse-card-note">' + html.escape(note) + "</div></div>")


# One thin bar for a part of the health score. In: name, points, most points. Out: nothing.
def health_bar(name, points, max_points):
    width = round(100 * points / max_points)
    show('<div class="pulse-bar-row"><div class="pulse-bar-top"><span>' + html.escape(name) + "</span>"
         "<span>" + str(round(points, 1)) + " / " + str(max_points) + "</span></div>"
         '<div class="pulse-bar"><div style="width:' + str(width) + '%"></div></div></div>')


# One item card in a maintainer queue. In: a queue entry from priority.py, accent name. Out: nothing.
def queue_item(entry, accent):
    kind = "Issue"
    if entry["is_pr"]:
        kind = "PR"
    show('<div class="pulse-item" style="--accent:var(--' + accent + ')">'
         '<a href="' + html.escape(entry["url"]) + '" target="_blank">#' + str(entry["number"]) + " "
         + html.escape(entry["title"]) + "</a>"
         '<div class="pulse-item-meta">' + kind + " · " + html.escape(entry["reason"]) + "</div>"
         '<div class="pulse-item-action">→ ' + html.escape(entry["next_action"]) + "</div></div>")


# A whole queue column: heading with count, then up to `limit` items. In: name, entries,
# accent name, limit. Out: nothing.
def queue_column(name, entries, accent, limit):
    show('<div class="pulse-queue-head">' + html.escape(name) + " · " + str(len(entries)) + "</div>")
    if len(entries) == 0:
        show('<div class="pulse-empty">Nothing here right now.</div>')
    for entry in entries[:limit]:
        queue_item(entry, accent)
