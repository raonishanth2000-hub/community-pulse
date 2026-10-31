# How the Pulse dashboard works

`pulse_dashboard.py` is Nishanth's version of the Community Pulse dashboard, built with
**Streamlit** (a Python library that turns a script into a web page). It's named differently
from the team's `dashboard.py`, so both can live in the repo without clashing.

```
pip3 install -r requirements.txt
streamlit run pulse_dashboard.py
```

It opens at `http://localhost:8501`. It reads the saved cache files, so no token is needed,
except for the optional **"Add a repo"** box, which downloads a new repo with your `.env` token.

## What's on the page

- **Sidebar.** Pick a repo, add a new one (with a live progress bar), and filter the waiting
  list: newcomers only, issues and/or PRs, a minimum number of days waiting, and a search box.
- **Banner.** The repo name, the dates the data covers, a status chip (Healthy / Needs care /
  At risk) and a **health ring** filled to the score.
- **Overview tab.** Four number cards, the four parts of the health score as bars, and a chart
  of how fast people got their first human reply.
- **Health score tab.** Each part of the score with a **"How is this worked out?"** button that
  shows the real number behind it and the rule. Next to it is a **"What if?"** panel: four sliders
  that change the inputs (first-reply time, review time, newcomers stuck, unanswered items) and
  show straight away what the score would become, and by how much.
- **Waiting tab.** A sortable table of every open item still waiting, with a bar showing how
  long, a link to GitHub, and who is waiting. The tab name shows the count after filtering.
- **Maintainer queues tab.** The three queues from `priority.py` as cards, each with its reason
  and next action.
- **Contributors tab.** The contributor funnel, plus the number of newcomers.

## The look

The dashboard has its own dark theme. All colours are defined once, at the top of
`pulse_style.css` (`:root`), and every other rule uses them by name, so one change there
updates the whole page. `.streamlit/config.toml` gives Streamlit's own buttons, sliders and
tables the same colours. The stylesheet also hides Streamlit's small "Press Enter to apply" hint
under text boxes, because the "Fetch it" button already makes the next step clear.

| Name | Colour | Used for |
|---|---|---|
| ink | `#0b0d1c` | page background |
| surface | `#14172e` | cards |
| violet | `#8b7cff` | brand colour, main chart colour |
| amber | `#cf7f26` | PR review card, "needs attention" queue |
| teal | `#16a07f` | newcomer card and queue |
| good / warning / critical | `#2bb673` / `#fab219` / `#e5534b` | health status only |

The chart colours were **checked with a colour-blindness validator** against the dark card
colour. They're far enough apart for people with colour blindness, bright enough against the
background, and the funnel uses one hue from light to dark, because its stages are in order.
Status colours always come with an icon and a word (● Healthy), never colour alone. Headings
use the *Space Grotesk* font and body text uses *Inter*.

## The animations (just a little)

All animation is plain CSS in `pulse_style.css`. There's no extra library.

- **Health ring.** It fills from empty to the score, and the number counts up from 0 at the same
  time, over 1.4 seconds. Then it gives a slow, soft glow every 3.2 seconds, like a heartbeat,
  which fits the name "Pulse". CSS normally can't animate a number, so `@property` *registers*
  `--fill` and `--num` as numbers. The browser then knows how to move them smoothly from 0 to the
  target. The number itself is drawn with a CSS counter (`content: counter(num)`).
- **Score bars** grow from the left (`transform: scaleX(0)` to full width).
- **Cards and queue items** fade up 8 pixels into place when the page loads. On hover, a card
  lifts slightly, and a queue item slides a little to the right.
- **Sidebar.** The brand dot beats gently, and the "N on" filter badge pops in.

The page-load animations use `backwards` timing, so they only affect the start. Once they finish,
hover effects work normally.

**Reduced motion.** If someone has turned on "Reduce motion" on their computer, every animation is
switched off (`prefers-reduced-motion`), and the ring and number simply show their final values.

## pulse_dashboard.py

This file only lays out the page. The contents of the tabs are in `pulse_tabs.py` and
`pulse_health.py`.

**`choose_repo(repos)`** decides which repo to show: one just added with "Add a repo" (saved as
`pending_repo`), otherwise the one picked before, otherwise fastapi/fastapi (or the first repo
there is). It sets the value **before** the repo dropdown is drawn, because Streamlit doesn't let
you change a dropdown afterwards.

**`newcomer_count(rows)`** counts how many waiting items were opened by newcomers, for the
sidebar's mini card.

**`main()`** builds the page from top to bottom. The sidebar gets the brand, the repo dropdown,
the mini health card, "Add a repo" and the filters. Then the main area gets the banner and the
five tabs. Streamlit runs the whole file again every time you change a filter. That's how the page
updates.

## pulse_tabs.py

**`hours_text(hours)`** shows a wait as short text: `5.6 h`, or `3.2 days` once it's over 48
hours, or `n/a` when there's no value.

**`overview_tab(numbers, items)`** draws the four number cards in a row, then two columns: the
health score parts as bars on the left, and the response-time chart on the right.

**`waiting_tab(rows)`** shows the filtered waiting list with `st.dataframe`. `column_config`
turns "days" into a bar (`ProgressColumn`) and "link" into a clickable "Open ↗"
(`LinkColumn`). `column_order` puts the link right after the title, so it's visible on small
screens. If nothing matches the filters, it says so in green.

**`queues_tab(items, repo)`** shows the three maintainer queues from `priority.py` side by
side.

**`contributors_tab(numbers)`** shows the funnel chart with the newcomer count beside it.

## pulse_health.py

The "Health score" tab. It uses the same rules and numbers as `health.py` and
`health_helpers.py`, so what you see always matches `python3 health.py`.

**`percent_text(share)`** and **`hours_text(hours)`** show a value as text, or "no data".

**`score_inputs(items, numbers)`** collects the four numbers the score is built from: the two
median waits (in hours), and the two shares (newcomer items stuck over 7 days, and open items
nobody has answered).

**`part_row(name, points, max_points, explanation)`** draws one part's bar, then a button
(`st.popover`) that opens a small box explaining that part.

**`parts_column(inputs, parts)`** draws all four parts. Each explanation includes the real number
(for example "Open items with no human reply or review at all: **43%**") and the rule that turns
it into points.

**`start_value(value, stand_in, largest)`** picks where a slider starts: today's real number
rounded to a whole number, or a stand-in when there's no data.

**`slider_score(first, review, stuck, unanswered)`** works out a score from the four slider
numbers, using `sliding_points` and `share_points` from `health_helpers.py`.

**`what_if_column(inputs, real_score, repo)`** draws the four sliders and the result. Sliders only
move in whole numbers, so their starting positions are slightly rounded (4.48% starts at 4%). If
we simply scored the slider values, the panel would show a small difference before you touched
anything. Instead it works out the **change** the sliders make (`slider_score` now minus
`slider_score` at the starting positions) and adds it to today's real score. Untouched sliders
therefore always show exactly today's score, and the change is grey; it turns green when the score
goes up and red when it goes down. Each slider has a `key` that includes the repo name, so every
repo keeps its own slider positions. Nothing is saved.

**`percent_number(share)`** turns a share like 0.43 into 43, leaving "no data" (`None`) alone.

**`health_tab(items, numbers, repo)`** puts the parts on the left and "What if?" on the right.

## pulse_sidebar.py

**`side(html_text)`** puts HTML in the sidebar instead of the main page.

**`brand()`** shows "Community Pulse" at the top of the sidebar, with a small teal dot that beats
like a pulse, and a thin line under it.

The sidebar has two sections, each with a small grey title in capitals: **REPOSITORY** (the
dropdown, the mini health card and "Add a repo") and **FILTER WAITING LIST** (search, newcomers
only, type, days waiting, and "Clear filters"). A thin line separates them.

**`section(title, badge)`** draws one of those small section titles. The badge (like "2 on") sits
at the right-hand end.

**`divider()`** draws the thin line between sections.

**`repo_picker(repos)`** draws the REPOSITORY title and the repo dropdown. The dropdown's own label
is hidden (`label_visibility="collapsed"`), because the section title already says what it is.

**`mini_card(score, word, status, waiting, newcomers_waiting)`** is a small card under the repo
dropdown: the score, its status chip, a bar, and how many people are waiting (and how many of them
are newcomers). Switch repos and it updates straight away.

**`fetch_box()`** is the "Add a repo" box (with a "+" icon from Streamlit's built-in icon set). It checks the name with `is_valid_repo`, then calls
`fetch_repo` from Stage 1 with a small function, `show_progress`, that moves a progress bar after
every step. If GitHub returns an error, the plain-English message is shown in red. When it
finishes, it reloads the page (`st.rerun()`) and the new repo is selected. Streamlit doesn't let you
change a dropdown after it's been drawn, and the repo dropdown is drawn before this box. So the box
saves the new name as `pending_repo`, and on the next run `main()` copies it into the dropdown's
value *before* drawing it.

**`FILTER_DEFAULTS`** lists each filter's starting value. Every filter widget has a `key`, which
links it to `st.session_state`, the dictionary where Streamlit remembers widget values.

**`clear_filters()`** sets every filter back to its starting value. It's given to the "Clear
filters" button as `on_click`, so Streamlit runs it *before* drawing the page again. That's the
only moment Streamlit allows changing a widget's value.

**`active_filter_count()`** counts how many filters differ from their starting value. For the
Type filter, the order doesn't matter ("PR, Issue" is the same as "Issue, PR").

**`filters()`** first fills in any missing starting values, then draws the divider and the
section title (with a violet "2 on" badge when filters are active). Then come the search box (with
a magnifying-glass icon and its label hidden, since the grey hint text says what it's for), the
"Newcomers only" switch, the Type buttons, the days slider, and the "Clear filters" button. The
button is greyed out when no filter is on.

## pulse_data.py

This file has no Streamlit in it. It reuses the functions from `metrics.py`, `health.py` and
`priority_helpers.py`, so the dashboard always shows the same numbers as the command-line tools.

**`summary(items)`** collects every headline number in one dictionary, so each is worked out
only once per page load.

**`health_label(score)`** turns the score into a word and a status: 80 or more is "Healthy", 50
or more is "Needs care", and below that is "At risk".

**`waiting_rows(items, repo)`** builds one table row for each item on `still_waiting_list`: who
opened it, whether they're a newcomer, whether it's waiting for a first reply or a review, how
many days, and a link.

**`filter_rows(rows, newcomers_only, kinds, min_days, search)`** keeps only the rows that match
the sidebar filters. The search ignores capitals and looks at the title and the author.

**`response_group(hours)`** and **`response_rows(items)`** sort first-response times into five
groups (under 1 hour up to over 7 days) and count each group for the chart.

**`funnel_rows(funnel)`** turns the three funnel numbers into chart rows in funnel order.

## pulse_charts.py

**`style(chart)`** gives every chart the same quiet look: transparent background, muted axis
labels and grid lines, and the Inter font.

**`funnel_chart(rows)`** draws horizontal bars, one per stage, with the number at the end of
each bar. Hovering a bar shows its exact value.

**`response_chart(rows)`** draws one violet bar per time group. Hovering shows the exact count.
Bars have rounded ends at the top only, so the bottom stays flat on the axis.

## pulse_parts.py

These build small bits of the page as HTML. **Every piece of text that comes from GitHub (titles,
names, reasons) goes through `html.escape`**, so a PR title containing `<` or `>` can't break the
page or add anything to it.

**`load_css()`** reads `pulse_style.css` and adds it to the page. **`show(html_text)`** puts HTML
on the page.

**`chip(word, status)`** makes the small status pill: an icon plus a word, in the status colour.

**`hero(repo, dates, score, word, status)`** draws the banner. The health ring is a CSS
`conic-gradient`: a circle coloured around its edge up to the score, like a pie chart with a hole
in the middle.

**`card(title, value, note, accent)`** draws one number card with a coloured line on top.

**`health_bar(name, points, max_points)`** draws one thin bar filled to `points / max_points`.

**`queue_item(entry, accent)`** and **`queue_column(name, entries, accent, limit)`** draw a
maintainer queue: a heading with the count, then up to 6 item cards, each with its reason and
next action.

## What it does NOT do

- It doesn't change anything on GitHub. The links only open pages.
- It has no light theme. It's designed dark on purpose.
- It doesn't use the Stage 8 guideline notes from Gemma yet.
- The fonts come from Google Fonts. Without internet, the page falls back to the normal system
  font and still works.
