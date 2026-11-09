"""Show Planner model: the same formulas as our analysis notebook, run on the numbers it exports (data.json).

Units = crowd x units per ticket x (new price / price paid before) ^ (elasticity x sensitivity)
Gross = units x price
"""
import json
import math
import pathlib

DATA = json.loads((pathlib.Path(__file__).parent / "data.json").read_text())
ITEMS = DATA["items"]
KEYS = [it["key"] for it in ITEMS]
NAMES = {it["key"]: it["name"] for it in ITEMS}
SHORT = {"water": "Water", "cocktail": "Cocktail", "fountain": "Fountain", "pretzel": "Pretzel", "michelob": "Michelob"}
GROUPS = DATA["groups"]
GROUP_COLORS = {"Family Day": "#1baf7a", "Family Night & Sports": "#eb6834", "Pop": "#6250d6",
                "Social": "#eda100", "Bar": "#2a78d6"}
GENRES = {"Concert": ["Rock", "Country", "Pop", "Hip-Hop / R&B", "Other"], "Comedy": ["Clean", "Moderate"],
          "Family": [], "Sports": ["Hockey", "Combat", "Other"]}
SENS_STEPS = [i / 20 for i in range(41)]          # 0x to 2x the published sensitivity


def jround(x):
    """Round half up (like JavaScript's Math.round), so every number matches our dashboard and CSV files."""
    return math.floor(x + 0.5)


def price_effect(item, price, paid, sens):
    return (price / paid) ** (DATA["elasticity"][item] * sens)


def forecast_show(show, card, scenario="base", sens=1.0):
    crowd = show["att"][scenario]
    out = {"crowd": crowd, "units": {}, "gross": 0.0, "gross_old": 0.0, "units_total": 0, "units_old": 0, "rows": []}
    for k in KEYS:
        b = show["items"][k]
        price = card[show["group"]][k]
        units = jround(crowd * b["perTicket"] * price_effect(k, price, b["paid"], sens))
        units_old = jround(crowd * b["perTicket"])
        gross = units * jround(price * 100) / 100
        out["units"][k] = units
        out["gross"] += gross
        out["gross_old"] += jround(units_old * b["paid"] * 100) / 100
        out["units_total"] += units
        out["units_old"] += units_old
        out["rows"].append({"event_id": show["e"], "item_name": NAMES[k], "projected_units": units,
                            "recommended_price": price, "projected_gross_sales": gross})
    return out


def forecast_all(card, scenario="base", sens=1.0):
    return [(s, forecast_show(s, card, scenario, sens)) for s in DATA["upcoming"]]


def totals(card, scenario="base", sens=1.0):
    fa = forecast_all(card, scenario, sens)
    return {"gross": sum(f["gross"] for _, f in fa), "gross_old": sum(f["gross_old"] for _, f in fa),
            "units": sum(f["units_total"] for _, f in fa), "units_old": sum(f["units_old"] for _, f in fa),
            "crowd": sum(f["crowd"] for _, f in fa)}


def past_test(card, sens=1.0):
    """Each past show's real units and sales, re-priced with the same formula (what our assumptions imply)."""
    out = {g: {"shows": 0, "u0": 0.0, "u1": 0.0, "g0": 0.0, "g1": 0.0} for g in GROUPS}
    for h in DATA["history"]:
        o = out[h["group"]]
        o["shows"] += 1
        for k in KEYS:
            u, gross = h["items"][k]
            if u <= 0:
                continue
            price = card[h["group"]][k]
            nu = u * price_effect(k, price, gross / u, sens)
            o["u0"] += u
            o["g0"] += gross
            o["u1"] += nu
            o["g1"] += nu * price
    return out


def place_show(kind, genre, male_share):
    """Our grouping rule, in order."""
    if kind == "Sports":
        return "Family Night & Sports", "A sports event goes to Family Night & Sports."
    if kind == "Family":
        if male_share >= 50:
            return "Family Night & Sports", "A family show whose buyers are mostly male goes to Family Night & Sports."
        return "Family Day", "A family show with mostly female or mixed buyers goes to Family Day."
    if kind == "Concert" and genre in ("Rock", "Country"):
        return "Bar", "A rock or country concert goes to Bar."
    if kind == "Concert" and genre == "Pop":
        return "Pop", "A pop concert goes to Pop."
    return "Social", "Hip-hop/R&B, comedy and other adult shows go to Social."


def plan_show(kind, genre, time, male_share, fans, card, sens=1.0):
    group, why = place_show(kind, genre, male_share)
    daytime_adult = time != "Evening" and kind != "Family"
    rows = []
    for k in KEYS:
        b = DATA["groupBasis"][group][k]
        per_ticket = b["perTicket"] * (DATA["dayVsEvening"][k] if daytime_adult else 1)
        price = card[group][k]
        units = jround(fans * per_ticket * price_effect(k, price, b["paid"], sens))
        rows.append({"key": k, "units": units, "price": price, "gross": units * price})
    return {"group": group, "why": why, "daytime_adult": daytime_adult, "rows": rows,
            "gross": sum(r["gross"] for r in rows)}


def sens_curve(card, scenario="base"):
    curve = []
    for s in SENS_STEPS:
        t = totals(card, scenario, s)
        curve.append({"s": s, "dg": t["gross"] - t["gross_old"], "rg": t["gross"] / t["gross_old"] - 1,
                      "du": t["units"] / t["units_old"] - 1})
    return curve


def break_even(curve, card, scenario="base"):
    """First sign change on the 0.05 grid, narrowed down by bisection. None if gross never crosses the old prices."""
    def dg_at(s):
        t = totals(card, scenario, s)
        return t["gross"] - t["gross_old"]
    for a, b in zip(curve, curve[1:]):
        if a["dg"] == 0:
            return a["s"]
        if (a["dg"] < 0) != (b["dg"] < 0):
            lo, hi, neg = a["s"], b["s"], a["dg"] < 0
            for _ in range(24):
                mid = (lo + hi) / 2
                if (dg_at(mid) < 0) == neg:
                    lo = mid
                else:
                    hi = mid
            return (lo + hi) / 2
    return None


PRESETS = {
    "Our card": lambda: {g: dict(DATA["defaultCard"][g]) for g in GROUPS},
    "What each group paid": lambda: {g: {k: jround(DATA["groupBasis"][g][k]["paid"] * 100) / 100 for k in KEYS} for g in GROUPS},
    "Current menu everywhere": lambda: {g: dict(DATA["menu"]) for g in GROUPS},
}


def forecast_csv(card, scenario="base", sens=1.0):
    lines = ["event_id,item_name,projected_units,recommended_price,projected_gross_sales"]
    for _, f in forecast_all(card, scenario, sens):
        for r in f["rows"]:
            lines.append(f'{r["event_id"]},{r["item_name"]},{r["projected_units"]},{r["recommended_price"]:.2f},{r["projected_gross_sales"]:.2f}')
    return "\n".join(lines) + "\n"


def groups_csv():
    rows = DATA["historicalGroups"] + [{"e": s["e"], "group": s["group"]} for s in DATA["upcoming"]]
    return "\n".join(["event_id,group"] + [f'{r["e"]},{r["group"]}' for r in rows]) + "\n"


def kind_label(s):
    if s["type"] == "Concert":
        return s["genre"]
    if s["type"] == "Comedy":
        return f'Comedy ({s["genre"].lower()})'
    if s["type"] == "Sports":
        return "Combat sports" if s["genre"] == "Combat" else s["genre"]
    return "Family show"
