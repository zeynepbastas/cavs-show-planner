"""Show Planner: place a show in one of our five crowd groups, forecast what its fans will buy, and test prices.

Run locally:  pip install -r requirements.txt  then  streamlit run streamlit_app.py
All numbers come from model.py, which uses the same formulas as our analysis notebook.
"""
import altair as alt
import pandas as pd
import streamlit as st

import model as M

st.set_page_config(page_title="Show Planner", layout="wide")

WINE, GOLD, GOLD_INK, LINE = "#6a0032", "#bb954c", "#8b6a2b", "#ece2e7"
COLOR_SCALE = alt.Scale(domain=M.GROUPS, range=[M.GROUP_COLORS[g] for g in M.GROUPS])

st.markdown(f"""<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@600;700;800&display=swap');
.block-container {{ padding-top: 2.2rem; max-width: 1200px; }}
.sp-head {{ text-align: center; padding-bottom: 1.3rem; border-bottom: 1px solid {LINE}; margin-bottom: 0.4rem; }}
.sp-head p {{ margin: 0 !important; }}
.sp-eyebrow {{ color: {GOLD_INK}; font-weight: 700; font-size: 0.78rem !important; letter-spacing: 0.18em; text-transform: uppercase; }}
.sp-title {{ font-family: 'Montserrat', sans-serif; color: {WINE}; font-weight: 800; font-size: clamp(2.3rem, 6vw, 3.7rem) !important;
  text-transform: uppercase; letter-spacing: 0.02em; line-height: 1.05 !important; padding-top: 0.35rem; }}
.sp-bar {{ width: 110px; height: 5px; border-radius: 3px; background: {GOLD}; margin: 0.9rem auto; }}
.sp-head .sp-lede {{ color: #51474c; max-width: 64ch; margin: 0 auto 0.7rem !important; }}
.sp-team {{ font-family: 'Montserrat', sans-serif; font-weight: 700; font-size: 1.25rem !important; display: flex; flex-wrap: wrap;
  justify-content: center; gap: 0.2rem 1.6rem; margin: 0; }}
.sp-head .sp-school {{ color: {GOLD_INK}; font-weight: 700; letter-spacing: 0.04em; margin-top: 0.3rem !important; }}
[data-testid="stMetricLabel"] p {{ color: {GOLD_INK}; text-transform: uppercase; letter-spacing: 0.08em; font-size: 0.72rem; font-weight: 700; }}
[data-testid="stMetricValue"] {{ font-family: 'Montserrat', sans-serif; color: {WINE}; font-weight: 800; font-size: 2rem !important; }}
.sp-h {{ font-family: 'Montserrat', sans-serif; color: {WINE}; text-transform: uppercase; letter-spacing: 0.03em;
  font-weight: 800; font-size: 1.1rem !important; margin: 0.4rem 0 0.2rem !important; }}
.sp-h::after {{ content: ""; display: block; width: 40px; height: 4px; border-radius: 2px; background: {GOLD}; margin-top: 0.45rem; }}
.sp-sum {{ border-left: 4px solid {GOLD}; background: #faf7f9; border-radius: 10px; padding: 0.9rem 1.2rem 0.5rem; margin: 0.4rem 0 1.1rem; }}
.sp-sum ol {{ margin: 0.5rem 0 0.3rem 1.1rem; padding: 0; }}
.sp-sum li {{ margin-bottom: 0.35rem; }}
.sp-sum li::marker {{ color: {GOLD_INK}; font-weight: 800; }}
.sp-verdict {{ border-left: 4px solid {GOLD}; background: #f6efe4; padding: 0.8rem 1rem; border-radius: 8px; margin-bottom: 0.8rem; }}
.sp-verdict .g {{ font-family: 'Montserrat', sans-serif; font-weight: 800; font-size: 1.35rem; }}
.sp-dot {{ display: inline-block; width: 12px; height: 12px; border-radius: 50%; margin-right: 8px; vertical-align: 1px; }}
</style>""", unsafe_allow_html=True)


def money0(v):
    return f"${M.jround(v):,}"


def signed(v):
    return "$0" if abs(v) < 0.5 else f"{'+' if v > 0 else '-'}${M.jround(abs(v)):,}"


def pct(v):
    return "0.0%" if abs(v) < 0.0005 else f"{'+' if v > 0 else ''}{v * 100:.1f}%"


def heading(text):
    st.markdown(f'<p class="sp-h">{text}</p>', unsafe_allow_html=True)


def dot(group):
    return f'<span class="sp-dot" style="background:{M.GROUP_COLORS[group]}"></span>'


# ---------- cover ----------
st.markdown("""<div class="sp-head">
<p class="sp-eyebrow">Concessions Pricing Challenge · Sports Business &amp; Analytics Night 2026</p>
<p class="sp-title">Show Planner</p><div class="sp-bar"></div>
<p class="sp-lede">Place any show in one of five crowd groups, forecast what its fans will buy, and test prices before the doors open.
Every number updates as you change the settings, starting from the choices our team made.</p>
<p class="sp-team"><span>Zeynep Baştaş</span><span>Blessing Masanga</span><span>Daniel Youngquist</span></p>
<p class="sp-school">Case Western Reserve University</p>
</div>""", unsafe_allow_html=True)

st.markdown("""<div class="sp-sum"><p class="sp-h">The short version</p><ol><li><b>Five crowd groups, one simple rule.</b> A sports event, or a family show where most buyers are men: Family Night &amp; Sports. Other family shows: Family Day. Rock or country concert: Bar. Pop concert: Pop. Everything else: Social.</li><li><b>The groups make forecasts more accurate.</b> Predicting each act from the other shows in its group cuts the error from 34% (no groups) to 22%.</li><li><b>Each crowd buys differently.</b> Bar crowds spend 7 times more on alcohol per fan than Family Day (&#36;13.30 vs &#36;1.80). Pop fans buy the most water, while hip-hop and comedy crowds lean on cocktails.</li><li><b>Prices flex by group.</b> Water &#36;4.99 everywhere, family prices for both family groups, today's menu for Pop and Social, and &#36;1.00 more on beer and &#36;2.20 more on cocktails for Bar.</li><li><b>For the 9 upcoming shows:</b> about the same money as today's prices (+0.2%) with 4.4% more items sold, at our card and the base crowd.</li></ol></div>""", unsafe_allow_html=True)

# ---------- settings ----------
SENS_OPTIONS = [0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0]
with st.sidebar:
    st.markdown('<p class="sp-h">Settings</p>', unsafe_allow_html=True)
    scenario = st.radio("Crowd size", ["Low", "Base", "High"], index=1, horizontal=True,
                        help="Base uses our Rule 2 attendance estimate. Low and high are the smallest and largest of our three rules.").lower()
    sens = st.select_slider("Price sensitivity", options=SENS_OPTIONS, value=1.0,
                            format_func=lambda s: "1x (published)" if s == 1 else f"{s:g}x",
                            help="How strongly fans react to price. 1x = the averages from published studies, 0x = fans ignore prices.")
    preset = st.radio("Start the price card from", list(M.PRESETS), index=0,
                      help="Our card is our recommendation. You can edit any price in the Price card tab.")

kpis = st.container()
tabs = st.tabs(["Price card", "Upcoming shows", "Plan a new show", "Price sensitivity", "Past shows", "How it works"])

# ---------- price card ----------
with tabs[0]:
    heading("Price card")
    st.caption("Type a price in any cell and every number in the app updates. The last column is today's menu price.")
    base = M.PRESETS[preset]()
    table = pd.DataFrame({g: [base[g][k] for k in M.KEYS] for g in M.GROUPS}, index=[M.NAMES[k] for k in M.KEYS])
    table["Menu now"] = [M.DATA["menu"][k] for k in M.KEYS]
    money_col = lambda g: st.column_config.NumberColumn(g, min_value=0.5, max_value=99.0, step=0.01, format="$%.2f")
    edited = st.data_editor(table, key=f"card::{preset}", disabled=["Menu now"], width="stretch",
                            column_config={**{g: money_col(g) for g in M.GROUPS}, "Menu now": money_col("Menu now")})
    card = {}
    for g in M.GROUPS:
        card[g] = {}
        for k in M.KEYS:
            v = edited.loc[M.NAMES[k], g]
            card[g][k] = float(v) if pd.notna(v) and v > 0 else base[g][k]

    st.caption("Change against what each group paid on average at past shows:")
    paid = pd.DataFrame({g: [card[g][k] / M.DATA["groupBasis"][g][k]["paid"] - 1 for k in M.KEYS] for g in M.GROUPS},
                        index=[M.NAMES[k] for k in M.KEYS])
    st.dataframe(paid.map(pct), width="stretch")

    heading("Last season at these prices")
    st.caption("What the 36 past shows would have sold at the prices above. It replays our price assumptions on real past "
               "sales, so it shows what the assumptions imply. The real test of the groups is the backtest in our notebook.")
    pt = M.past_test(card, sens)
    rows = [{"Group": g, "Past shows": o["shows"], "Items sold": M.jround(o["u0"]),
             "Items, new prices": pct(o["u1"] / o["u0"] - 1), "Gross, real": money0(o["g0"]),
             "Gross, new prices": money0(o["g1"]), "Change": f'{signed(o["g1"] - o["g0"])} ({pct(o["g1"] / o["g0"] - 1)})'}
            for g, o in pt.items()]
    t = {k: sum(o[k] for o in pt.values()) for k in ("u0", "u1", "g0", "g1")}
    rows.append({"Group": "All 36 shows", "Past shows": 36, "Items sold": M.jround(t["u0"]), "Items, new prices": pct(t["u1"] / t["u0"] - 1),
                 "Gross, real": money0(t["g0"]), "Gross, new prices": money0(t["g1"]),
                 "Change": f'{signed(t["g1"] - t["g0"])} ({pct(t["g1"] / t["g0"] - 1)})'})
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")

# ---------- headline numbers ----------
fa = M.forecast_all(card, scenario, sens)
tot = M.totals(card, scenario, sens)
low, high = M.totals(card, "low", sens), M.totals(card, "high", sens)
with kpis:
    c = st.columns([1, 1, 1, 1.35])
    c[0].metric("Gross, 9 shows, 5 items", money0(tot["gross"]), f'{pct(tot["gross"] / tot["gross_old"] - 1)} vs old prices',
                help=f'Old prices: {money0(tot["gross_old"])} for the same crowd.')
    c[1].metric("Items sold", f'{tot["units"]:,}', f'{pct(tot["units"] / tot["units_old"] - 1)} vs old prices')
    c[2].metric("Crowd, all 9 shows", f'{tot["crowd"]:,}', {"low": "Low scenario", "base": "Base case (Rule 2)", "high": "High scenario"}[scenario],
                delta_color="off", delta_arrow="off")
    c[3].metric("Gross range, low to high crowd", f'${M.jround(low["gross"] / 1000)}K to ${M.jround(high["gross"] / 1000)}K', "At these prices",
                delta_color="off", delta_arrow="off")

# ---------- upcoming shows ----------
with tabs[1]:
    heading("The 9 upcoming shows")
    lows = {s["e"]: f["gross"] for s, f in M.forecast_all(card, "low", sens)}
    highs = {s["e"]: f["gross"] for s, f in M.forecast_all(card, "high", sens)}
    chart_df = pd.DataFrame([{"Show": f'{s["e"]} · {s["p"]} · {M.kind_label(s)}', "Group": s["group"], "Gross": f["gross"],
                              "Low": lows[s["e"]], "High": highs[s["e"]], "Label": f'${f["gross"] / 1000:.1f}K'} for s, f in fa])
    order = list(chart_df["Show"])
    y = alt.Y("Show:N", sort=order, title=None, axis=alt.Axis(labelLimit=260))
    rng = alt.Chart(chart_df).mark_rule(color="#85797f", strokeWidth=2).encode(
        y=y, x=alt.X("Low:Q", title="Gross for the five items ($)", axis=alt.Axis(format="$,.0f")), x2="High:Q")
    pts = alt.Chart(chart_df).mark_circle(size=170, opacity=1, stroke="white", strokeWidth=2).encode(
        y=y, x="Gross:Q", color=alt.Color("Group:N", scale=COLOR_SCALE, legend=alt.Legend(orient="bottom", title=None)),
        tooltip=["Show", "Group", alt.Tooltip("Gross:Q", format="$,.0f"), alt.Tooltip("Low:Q", format="$,.0f"), alt.Tooltip("High:Q", format="$,.0f")])
    lbl = alt.Chart(chart_df).mark_text(align="left", dx=10, fontWeight="bold").encode(y=y, x="High:Q", text="Label:N")
    st.altair_chart((rng + pts + lbl).properties(height=330), width="stretch")
    st.caption("Dot: gross for the five items at your prices and crowd size. Line: low to high crowd.")

    rows = []
    for s, f in fa:
        rows.append({"Show": f'{s["e"]} ({s["p"]}, {s["day"][:3]} {s["time"].lower()})', "Group": s["group"], "Crowd": f["crowd"],
                     **{M.SHORT[k]: f["units"][k] for k in M.KEYS}, "Gross": money0(f["gross"]),
                     "vs old prices": signed(f["gross"] - f["gross_old"]),
                     "Based on": ("Own past shows" + (f', {s["note"]}' if s["note"] else "")) if s["basis"] == "own" else "Group average"})
    rows.append({"Show": "Total", "Group": "", "Crowd": tot["crowd"], **{M.SHORT[k]: sum(f["units"][k] for _, f in fa) for k in M.KEYS},
                 "Gross": money0(tot["gross"]), "vs old prices": signed(tot["gross"] - tot["gross_old"]), "Based on": ""})
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")

# ---------- plan a new show ----------
with tabs[2]:
    heading("Plan a new show")
    st.caption("Our grouping rule on a show that is not on the schedule yet.")
    left, right = st.columns([1, 2], gap="large")
    with left:
        kind = st.selectbox("Event type", ["Concert", "Comedy", "Family", "Sports"])
        genre = st.selectbox("Genre", M.GENRES[kind], index=1 if kind == "Concert" else 0) if M.GENRES[kind] else ""
        time = st.selectbox("Start time", ["Evening", "Afternoon", "Morning"])
        male = st.slider("Male share of ticket buyers", 0, 100, 45, format="%d%%") if kind == "Family" else 45
        fans = st.number_input("Expected crowd", min_value=0, max_value=25000, value=11000, step=100)
    with right:
        r = M.plan_show(kind, genre, time, male, fans, card, sens)
        st.markdown(f'<div class="sp-verdict">{dot(r["group"])}<span class="g">{r["group"]}</span><br>{r["why"]} '
                    f'Past shows in this group spent ${M.DATA["groupStats"][r["group"]]["alc"]:.1f} a head on alcohol.</div>',
                    unsafe_allow_html=True)
        plan = pd.DataFrame([{"Item": M.NAMES[x["key"]], "Price": f'${x["price"]:.2f}', "Units": f'{x["units"]:,}', "Gross": money0(x["gross"])}
                             for x in r["rows"]] + [{"Item": "Total", "Price": "", "Units": f'{sum(x["units"] for x in r["rows"]):,}', "Gross": money0(r["gross"])}])
        st.dataframe(plan, hide_index=True, width="stretch")
        note = f'That is ${r["gross"] / fans:.2f} per fan on these five items.' if fans else ""
        if r["daytime_adult"]:
            note += " Daytime adult show: units are adjusted with P25's daytime/evening ratios (much less alcohol, more water and pretzels)."
        st.caption(note + " Prices come from the price card.")

# ---------- price sensitivity ----------
with tabs[3]:
    heading("What if fans react more or less to price?")
    st.caption("Our data can't measure price sensitivity, because the menu price was the same at every past show. So we borrow it "
               "from published studies. These charts run the price card with sensitivity anywhere from 0x (fans ignore prices) "
               "to 2x the published values.")
    curve = M.sens_curve(card, scenario)
    be = M.break_even(curve, card, scenario)
    at = {round(c["s"], 2): c for c in curve}
    m0, m1 = at[0.0], at[1.0]
    if be is None:
        lead = ("This card makes at least as much as the old prices at every sensitivity from 0x to 2x." if m0["dg"] >= 0
                else "This card brings in less than the old prices at every sensitivity from 0x to 2x.")
    elif m0["dg"] < 0:
        lead = f"This card breaks even at {be:.2f}x the published sensitivity and makes more above that."
    else:
        lead = f"This card makes more than the old prices up to {be:.2f}x the published sensitivity, and less above that."
    st.markdown(f'{lead} If fans ignore prices completely: **{signed(m0["dg"])}** ({m0["rg"] * 100:+.2f}%). '
                f'At the published values: **{signed(m1["dg"])}** ({m1["rg"] * 100:+.2f}%), and items sold go '
                f'{"up" if m1["du"] >= 0 else "down"} {abs(m1["du"] * 100):.1f}%.')
    cdf = pd.DataFrame(curve)
    cur = cdf[(cdf.s - sens).abs() < 1e-9]
    x = alt.X("s:Q", title="Price sensitivity (1 = published studies)", scale=alt.Scale(domain=[0, 2]))
    zero = alt.Chart(pd.DataFrame({"z": [0]})).mark_rule(color="#85797f").encode(y="z:Q")
    g1 = alt.Chart(cdf).mark_line(color=WINE, strokeWidth=2.5).encode(x=x, y=alt.Y("dg:Q", title="Gross vs old prices ($)", axis=alt.Axis(format="$,.0f")),
                                                                    tooltip=[alt.Tooltip("s:Q", title="Sensitivity"), alt.Tooltip("dg:Q", format="$,.0f", title="Gross vs old")])
    g1p = alt.Chart(cur).mark_circle(color=WINE, size=110).encode(x="s:Q", y="dg:Q")
    layers = [zero, g1, g1p]
    if be is not None:
        layers.append(alt.Chart(pd.DataFrame({"s": [be], "t": [f"break-even {be:.2f}x"]})).mark_rule(color=GOLD, strokeDash=[4, 3]).encode(x="s:Q"))
    i1 = alt.Chart(cdf).mark_line(color=WINE, strokeWidth=2.5).encode(x=x, y=alt.Y("du:Q", title="Items sold vs old prices", axis=alt.Axis(format="+.0%")),
                                                                    tooltip=[alt.Tooltip("s:Q", title="Sensitivity"), alt.Tooltip("du:Q", format="+.1%", title="Items vs old")])
    i1p = alt.Chart(cur).mark_circle(color=WINE, size=110).encode(x="s:Q", y="du:Q")
    a, b = st.columns(2, gap="large")
    a.altair_chart(alt.layer(*layers).properties(height=280, title="Gross sales vs old prices"), width="stretch")
    b.altair_chart(alt.layer(zero, i1, i1p).properties(height=280, title="Items sold vs old prices"), width="stretch")
    st.caption("The dot is the sensitivity picked in the settings. The dashed gold line is the break-even point.")
    with st.expander("Show the numbers"):
        st.dataframe(pd.DataFrame([{"Price sensitivity": "1x (published)" if c["s"] == 1 else f'{c["s"]:g}x',
                                    "Gross vs old prices": f'{signed(c["dg"])} ({c["rg"] * 100:+.2f}%)', "Items sold vs old prices": pct(c["du"])}
                                   for c in curve if round(c["s"], 2) in SENS_OPTIONS]), hide_index=True, width="stretch")

# ---------- past shows ----------
with tabs[4]:
    heading("Past shows by group")
    st.caption("Each panel lights up one group; the gray dots are all the other past shows. Across: alcohol per ticket. "
               "Up: food and soft drinks per ticket. Hover a dot for the show.")
    hist = pd.DataFrame([{"Show": h["e"], "Performer": h["p"], "Kind": M.kind_label(h), "Group": h["group"], "Tickets": h["tickets"],
                          "Alcohol per fan": h["alc"], "Food and soft drinks per fan": h["oth"], "All concessions per fan": h["spend"]}
                         for h in M.DATA["history"]])
    long = pd.concat([hist.assign(Panel=g, Lit=hist.Group.eq(g)) for g in M.GROUPS], ignore_index=True)
    base_enc = dict(x=alt.X("Alcohol per fan:Q", title="Alcohol per ticket ($)", scale=alt.Scale(domain=[0, 21])),
                    y=alt.Y("Food and soft drinks per fan:Q", title="Food + soft drinks per ticket ($)", scale=alt.Scale(domain=[2, 10], clamp=True)))
    gray = alt.Chart().mark_circle(size=45, color="#85797f", opacity=0.3).encode(**base_enc).transform_filter("!datum.Lit")
    lit = alt.Chart().mark_circle(size=110, opacity=1, stroke="white", strokeWidth=1.5).encode(
        **base_enc, color=alt.Color("Group:N", scale=COLOR_SCALE, legend=None),
        tooltip=["Show", "Performer", "Kind", alt.Tooltip("Tickets:Q", format=","), alt.Tooltip("Alcohol per fan:Q", format="$.2f"),
                 alt.Tooltip("Food and soft drinks per fan:Q", format="$.2f")]).transform_filter("datum.Lit")
    facet = alt.layer(gray, lit, data=long).properties(width=255, height=200).facet(
        facet=alt.Facet("Panel:N", sort=M.GROUPS, title=None, header=alt.Header(labelFontWeight="bold", labelFontSize=13)), columns=3)
    st.altair_chart(facet, width="content")
    with st.expander("Show the numbers"):
        st.dataframe(hist.sort_values(["Group", "Alcohol per fan"], ascending=[True, False]), hide_index=True, width="stretch",
                     column_config={c: st.column_config.NumberColumn(format="$%.2f") for c in ["Alcohol per fan", "Food and soft drinks per fan", "All concessions per fan"]})

# ---------- how it works ----------
with tabs[5]:
    heading("How the numbers are built")
    st.markdown("""
- **Groups**, in order: a sports event, or a family show where at least half the ticket buyers are men = **Family Night & Sports**;
  other family shows = **Family Day**; rock or country concert = **Bar**; pop concert = **Pop**; everything else (hip-hop/R&B, comedy) = **Social**.
- **Units** = crowd x units per ticket x (new price / price paid before) ^ elasticity. **Gross** = units x price.
- **Units per ticket** come from the performer's own past shows when they played here before (P03, P06, P19, P33), otherwise from their group.
  E111 and E155 change between daytime and evening, so they get P25's daytime/evening ratios.
- **Crowd:** base = Rule 2. High = the largest of Rules 1 to 3. Low = the smallest, except repeat acts get 75% of their past crowd,
  never below tickets already sold.
- **The real test** is the backtest in our notebook: hide one act's shows, predict them from the other shows in the same group,
  and compare with what they actually sold. Error: 34.0% with no groups, 24.0% with our first 4 groups, 21.8% with the 5 groups.
- **Price sensitivity:** menu prices never changed in the data, so we can't measure it ourselves. We use published averages:
  beer -0.46, spirits -0.80 ([Wagenaar et al., 2009](https://movendi.ngo/science-digest/effects-of-beverage-alcohol-price-and-tax-levels-on-alcohol-use/)),
  soft drinks -0.79 and food away from home -0.81 ([Andreyeva et al., 2010](https://scholars.duke.edu/publication/963616)).
  The sensitivity setting scales all of them.
- Concessions data covers most but not all points of sale, so treat totals as a consistent measure, not the arena's full revenue.
""")

# ---------- files ----------
with st.sidebar:
    st.divider()
    st.markdown('<p class="sp-h">Download the CSVs</p>', unsafe_allow_html=True)
    st.download_button("upcoming_forecast.csv", M.forecast_csv(card, scenario, sens), file_name="upcoming_forecast.csv",
                       mime="text/csv", type="primary", width="stretch")
    st.download_button("event_groups.csv", M.groups_csv(), file_name="event_groups.csv", mime="text/csv", width="stretch")
    st.caption("Saves what the app shows now. Our submitted files use Our card, Base crowd and 1x sensitivity.")
