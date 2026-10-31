# pulse_charts.py - The two charts on the Pulse dashboard, drawn with Altair
# (a chart library that comes with Streamlit). Hovering a bar shows its exact number.
# Colours match pulse_style.css and were checked for colour-blind safety on the dark surface.

import altair as alt

VIOLET = "#8b7cff"
FUNNEL_COLOURS = ["#c2b8ff", "#8b7cff", "#5b4fd6"]  # one hue, light to dark, for the 3 stages
MUTED = "#9a9fc4"
GRID = "#2a2f55"


# Applies the dashboard's quiet axis and grid style to a chart. In: chart. Out: styled chart.
def style(chart):
    return (chart.properties(background="transparent")
            .configure_view(strokeWidth=0)
            .configure_axis(labelColor=MUTED, titleColor=MUTED, gridColor=GRID, domainColor=GRID,
                            tickColor=GRID, labelFont="Inter", titleFont="Inter", labelFontSize=12)
            .configure_text(font="Inter"))


# Horizontal bars for the contributor funnel, with the number written at the end of each bar.
# In: rows from pulse_data.funnel_rows. Out: an Altair chart.
def funnel_chart(rows):
    base = alt.Chart(alt.Data(values=rows)).encode(
        y=alt.Y("stage:N", sort=alt.SortField("order"), title=None, axis=alt.Axis(labelLimit=220)),
        x=alt.X("people:Q", title="People", axis=alt.Axis(tickCount=5)),
        tooltip=[alt.Tooltip("stage:N", title="Stage"), alt.Tooltip("people:Q", title="People")])
    bars = base.mark_bar(cornerRadiusEnd=4, height=26).encode(
        color=alt.Color("stage:N", sort=alt.SortField("order"), legend=None,
                        scale=alt.Scale(range=FUNNEL_COLOURS)))
    labels = base.mark_text(align="left", dx=6, color="#e8e9f5", fontWeight=600).encode(text="people:Q")
    return style((bars + labels).properties(height=170))


# Vertical bars: how long items waited for their first human reply.
# In: rows from pulse_data.response_rows. Out: an Altair chart.
def response_chart(rows):
    chart = alt.Chart(alt.Data(values=rows)).mark_bar(cornerRadiusEnd=4, width=34, color=VIOLET).encode(
        x=alt.X("group:N", sort=alt.SortField("order"), title="Time to first human reply",
                axis=alt.Axis(labelAngle=0)),
        y=alt.Y("items:Q", title="Items"),
        tooltip=[alt.Tooltip("group:N", title="Replied within"), alt.Tooltip("items:Q", title="Items")])
    return style(chart.properties(height=240))
