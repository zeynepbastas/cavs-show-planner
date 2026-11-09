#!/usr/bin/env python3
"""
Rocket Arena concessions forecast
=================================
Places every show into one of five groups, then forecasts units sold for each
of the five top concession items at every upcoming show.

Usage
-----
    python forecast_upcoming.py                      # CSVs in the same folder
    python forecast_upcoming.py --data-dir path/to/csvs --out-dir path/to/out
    python forecast_upcoming.py --backtest           # also print accuracy tests

Outputs
-------
    event_groups.csv        group for every historical and upcoming show
    upcoming_forecast.csv   projected units / price / gross sales per show x item

GROUPING RULES (applied in this order, first match wins)
--------------------------------------------------------
  1. Sports event, OR a Family show where >= 50% of the performer's
     buyers are men                              -> "Family Night & Sports"
  2. Any other Family show                       -> "Family Day"
  3. Rock or Country concert                     -> "Bar"
  4. Pop concert                                 -> "Pop"
  5. Everything else (Hip-Hop/R&B, Comedy)       -> "Social"
  A Family performer with no demographic data is treated as "other Family".

FORECAST METHOD
---------------
  units = projected_attendance x group units-per-ticket (per item)

  * units-per-ticket: average, across the historical shows in the group, of
    (item units sold / tickets sold). Shows where an item sold 0 count as 0.
  * projected_attendance: the performer's own historical average attendance
    if they have played before, otherwise the median attendance of the group.
    It is never lower than tickets_sold_to_date.
  * price: recommended price = current price x (1 + group/item step) -- see
    PRICING below. Units are then adjusted for the price change with a
    constant-elasticity demand curve:  units = base_units x (new/old)^elasticity.

PRICING (ASSUMPTION-BASED -- historical prices never varied)
------------------------------------------------------------
  Every item sold at one price at every past show, so price sensitivity cannot
  be measured from the data. Elasticities below are ASSUMPTIONS, not estimates.
  effective elasticity = BASE_ELASTICITY[item] x GROUP_SENSITIVITY[group]
  Step rule (non-Family groups): |e| <= 0.45 -> +10%, <= 0.75 -> +5%, else hold.
  Water is capped at +5%. Family groups are held at the current price.
  Prices are rounded to the nearest $0.05.
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

# ----------------------------------------------------------------------------
# Settings
# ----------------------------------------------------------------------------
MALE_SHARE_CUTOFF = 0.50
GROUP_ORDER = ["Family Night & Sports", "Family Day", "Pop", "Bar", "Social"]

# "history_then_group": performer's past average attendance, else group median
# "group_median":       group median attendance only
ATTENDANCE_METHOD = "history_then_group"

# --- Pricing assumptions (see PRICING in the docstring) ---------------------
BASE_ELASTICITY = {            # change in units for a 1% change in price
    "20oz Dasani Water": -0.35,    # necessity, captive audience
    "24oz Fountain Drink": -0.50,
    "Bavarian Pretzel": -0.70,     # discretionary food
    "16oz Michelob Ultra": -0.80,  # already $16.99, close substitutes exist
    "Double Cocktail": -0.60,
}
GROUP_SENSITIVITY = {          # >1 = more price sensitive than average
    "Bar": 0.8, "Social": 1.0, "Pop": 1.0,
    "Family Day": 1.4, "Family Night & Sports": 1.2,
}
HOLD_GROUPS = ("Family Day", "Family Night & Sports")   # no increases
WATER_MAX_STEP = 0.05
SCENARIO_MULTIPLIERS = (0.5, 1.0, 1.5, 2.0)   # scale every elasticity


# ----------------------------------------------------------------------------
# Loading
# ----------------------------------------------------------------------------
def load(data_dir: Path):
    hist = pd.read_csv(data_dir / "historical_events.csv")
    up = pd.read_csv(data_dir / "upcoming_events.csv")
    items = pd.read_csv(data_dir / "concessions_top5_overall_items.csv")
    by_event = pd.read_csv(data_dir / "concessions_top5_overall_by_event.csv")
    profile = pd.read_csv(data_dir / "performer_demographic_profile.csv")
    return hist, up, items, by_event, profile


def male_share_by_performer(profile: pd.DataFrame) -> pd.Series:
    g = (profile[profile["dimension"] == "gender"]
         .pivot_table(index="performer_id", columns="value",
                      values="buyer_count", aggfunc="sum"))
    return g["M"] / (g["M"] + g["F"])


# ----------------------------------------------------------------------------
# Grouping
# ----------------------------------------------------------------------------
def assign_group(row, male_share: pd.Series):
    """Return (group, rule_text) for one show."""
    if row["event_type"] == "Sports":
        return "Family Night & Sports", "Rule 1: Sports event"
    if row["event_type"] == "Family":
        share = male_share.get(row["performer_id"], np.nan)
        if pd.notna(share) and share >= MALE_SHARE_CUTOFF:
            return ("Family Night & Sports",
                    f"Rule 1: Family show, {share:.0%} male buyers")
        why = "no demographic data" if pd.isna(share) else f"{share:.0%} male buyers"
        return "Family Day", f"Rule 2: other Family show ({why})"
    if row["genre"] in ("Rock", "Country"):
        return "Bar", "Rule 3: Rock or Country concert"
    if row["genre"] == "Pop":
        return "Pop", "Rule 4: Pop concert"
    return "Social", "Rule 5: everything else (Hip-Hop/R&B, Comedy)"


def add_groups(df: pd.DataFrame, male_share: pd.Series) -> pd.DataFrame:
    out = df.copy()
    res = out.apply(lambda r: assign_group(r, male_share), axis=1)
    out["group"] = [r[0] for r in res]
    out["rule_applied"] = [r[1] for r in res]
    return out


# ----------------------------------------------------------------------------
# Forecast pieces
# ----------------------------------------------------------------------------
def units_per_ticket(train: pd.DataFrame, units_wide: pd.DataFrame) -> pd.DataFrame:
    """Group x item table of average units per ticket (train = grouped hist)."""
    rates = units_wide.loc[train["event_id"]].div(train["tickets_sold"].values, axis=0)
    rates.index = train["event_id"]
    return rates.groupby(train.set_index("event_id")["group"]).mean()


def projected_attendance(row, train: pd.DataFrame, to_date: float = 0.0,
                         method: str = ATTENDANCE_METHOD) -> float:
    same_perf = train[train["performer_id"] == row["performer_id"]]
    if method == "history_then_group" and len(same_perf):
        est = same_perf["tickets_sold"].mean()
    else:
        pool = train[train["group"] == row["group"]]["tickets_sold"]
        est = pool.median() if len(pool) else train["tickets_sold"].median()
    return max(est, to_date)


def forecast_units(attendance: float, group: str, rates: pd.DataFrame) -> pd.Series:
    r = rates.loc[group] if group in rates.index else rates.mean()
    return attendance * r


# ----------------------------------------------------------------------------
# Pricing
# ----------------------------------------------------------------------------
def effective_elasticity(item: str, group: str) -> float:
    return BASE_ELASTICITY[item] * GROUP_SENSITIVITY[group]


def recommend_price(item: str, group: str, current: float) -> float:
    # Hard-coded pricing strategy based on the latest "Best of both" card
    # Water: $4.99 at every show
    if item == "20oz Dasani Water":
        return 4.99

    # Family groups: held at current price (family deals)
    if group in HOLD_GROUPS:
        return float(current)

    # Bar crowds (rock/country): cocktail $30.99, Michelob $17.99
    if group == "Bar":
        if item == "Double Cocktail":
            return 30.99
        if item == "16oz Michelob Ultra":
            return 17.99

    # Pop and Social crowds: cocktail $30.25, Michelob $17.49
    if group in ("Pop", "Social"):
        if item == "Double Cocktail":
            return 30.25
        if item == "16oz Michelob Ultra":
            return 17.49

    # Default: hold current price for everything else
    return float(current)


def units_at_price(base_units: float, item: str, group: str, old: float,
                   new: float, multiplier: float = 1.0) -> float:
    e = effective_elasticity(item, group) * multiplier
    return base_units * (new / old) ** e


# ----------------------------------------------------------------------------
# Backtest (leave one historical show out)
# ----------------------------------------------------------------------------
def backtest(hist_g: pd.DataFrame, units_wide: pd.DataFrame, method: str) -> dict:
    rate_err, full_err, att_err = [], [], []
    for e in hist_g["event_id"]:
        train = hist_g[hist_g["event_id"] != e]
        row = hist_g[hist_g["event_id"] == e].iloc[0]
        rates = units_per_ticket(train, units_wide)
        actual = units_wide.loc[e].sum()
        # a) attendance known -> pure grouping error
        p1 = forecast_units(row["tickets_sold"], row["group"], rates).sum()
        # b) attendance projected -> realistic error for a future show
        att = projected_attendance(row, train, method=method)
        p2 = forecast_units(att, row["group"], rates).sum()
        rate_err.append(abs(p1 - actual) / actual)
        full_err.append(abs(p2 - actual) / actual)
        att_err.append(abs(att - row["tickets_sold"]) / row["tickets_sold"])
    f = lambda x: f"{np.mean(x):.1%} mean / {np.median(x):.1%} median"
    return {"units error, attendance known": f(rate_err),
            "attendance error": f(att_err),
            "units error, attendance projected": f(full_err)}


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------
def main():
    here = Path(__file__).resolve().parent
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", type=Path, default=here)
    ap.add_argument("--out-dir", type=Path, default=here)
    ap.add_argument("--backtest", action="store_true")
    args = ap.parse_args()

    hist, up, items, by_event, profile = load(args.data_dir)
    male = male_share_by_performer(profile)
    hist_g, up_g = add_groups(hist, male), add_groups(up, male)

    units_wide = (by_event.pivot(index="event_id", columns="item_name",
                                 values="units_sold").fillna(0))
    item_order = items.sort_values("overall_rank")["item_name"].tolist()
    units_wide = units_wide[item_order]
    price = items.set_index("item_name")["current_price"]

    # ---- event_groups.csv
    cols = ["event_id", "group", "rule_applied", "performer_id",
            "event_type", "genre"]
    groups_out = pd.concat([hist_g.assign(status="historical"),
                            up_g.assign(status="upcoming")])[cols + ["status"]]
    groups_out.to_csv(args.out_dir / "event_groups.csv", index=False)

    # ---- upcoming_forecast.csv
    rates = units_per_ticket(hist_g, units_wide)
    rows = []
    for _, ev in up_g.iterrows():
        att = projected_attendance(ev, hist_g, ev["tickets_sold_to_date"])
        base = forecast_units(att, ev["group"], rates)
        for item in item_order:
            p0 = float(price[item])
            p1 = recommend_price(item, ev["group"], p0)
            u = int(round(units_at_price(base[item], item, ev["group"], p0, p1)))
            rows.append({"event_id": ev["event_id"], "item_name": item,
                         "projected_units": u, "recommended_price": p1,
                         "projected_gross_sales": round(u * p1, 2),
                         "group": ev["group"],
                         "projected_attendance": int(round(att)),
                         "current_price": p0,
                         "price_change_pct": round((p1 / p0 - 1) * 100, 1),
                         "baseline_units": int(round(base[item]))})
    fc = pd.DataFrame(rows)
    fc.to_csv(args.out_dir / "upcoming_forecast.csv", index=False)

    # ---- pricing_by_group.csv (per group x item, at one show's attendance)
    pg = (fc.groupby(["group", "item_name"])
            .agg(current_price=("current_price", "first"),
                 recommended_price=("recommended_price", "first"),
                 price_change_pct=("price_change_pct", "first"),
                 baseline_units=("baseline_units", "sum"),
                 projected_units=("projected_units", "sum"),
                 baseline_gross=("current_price",
                                 lambda x: 0.0)).reset_index())
    pg["baseline_gross"] = (pg["baseline_units"] * pg["current_price"]).round(2)
    pg["projected_gross"] = (pg["projected_units"] * pg["recommended_price"]).round(2)
    pg["assumed_elasticity"] = [round(effective_elasticity(i, g), 2)
                                for g, i in zip(pg["group"], pg["item_name"])]
    pg.to_csv(args.out_dir / "pricing_by_group.csv", index=False)

    # ---- scenario table (all nine upcoming shows combined)
    scen = []
    for mult in SCENARIO_MULTIPLIERS:
        u1 = sum(units_at_price(r.baseline_units, r.item_name, r.group,
                                r.current_price, r.recommended_price, mult)
                 for r in fc.itertuples())
        g1 = sum(units_at_price(r.baseline_units, r.item_name, r.group,
                                r.current_price, r.recommended_price, mult)
                 * r.recommended_price for r in fc.itertuples())
        g0 = (fc["baseline_units"] * fc["current_price"]).sum()
        scen.append({"elasticity_x": mult,
                     "units_change": f"{u1 / fc['baseline_units'].sum() - 1:+.1%}",
                     "gross_change": f"{g1 / g0 - 1:+.1%}",
                     "gross_change_$": round(g1 - g0)})
    scen = pd.DataFrame(scen)

    print("Groups (upcoming shows):")
    print(up_g[["event_id", "performer_id", "genre", "group", "rule_applied"]]
          .to_string(index=False))
    print("\nForecast totals per show:")
    print(fc.groupby("event_id")
            .agg(group=("group", "first"),
                 attendance=("projected_attendance", "first"),
                 units=("projected_units", "sum"),
                 gross=("projected_gross_sales", "sum")).to_string())

    print("\nPrice-change scenarios (elasticity_x scales every assumed elasticity):")
    print(scen.to_string(index=False))

    if args.backtest:
        print("\nBacktest (leave one historical show out, top-5 items total):")
        for m in ("group_median", "history_then_group"):
            print(f"  attendance method = {m}")
            for k, v in backtest(hist_g, units_wide, m).items():
                print(f"    {k}: {v}")


if __name__ == "__main__":
    main()
