"""Rebuild data.json (the numbers the app uses) from our analysis notebook.

Usage, from this folder:  put the 8 challenge CSV files in a folder called data, then run  python make_app_data.py
It runs the notebook's code through section 8 and saves group rates, past shows and the 9 upcoming shows at full precision.
"""
import contextlib
import io
import json

import pathlib

NB = next(p for p in [pathlib.Path("analysis/CWRU_Concessions_Analysis.ipynb"), pathlib.Path("../CWRU_Concessions_Analysis.ipynb")] if p.exists())
nb = json.load(open(NB))
cells = ["".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code"]
env = {"display": lambda *a, **k: None}
with contextlib.redirect_stdout(io.StringIO()):
    for src in cells[:10]:          # through section 8 (forecast at our price card)
        exec(compile(src, "notebook", "exec"), env)

m, up = env["m"].sort_values("event_id"), env["up"].sort_values("event_id")
ITEM_ORDER, ITEMS = env["ITEM_ORDER"], env["ITEMS"]
GROUPS, CARD = env["GROUP_ORDER"], env["PRICE_CARD"]
name_of = {v: k for k, v in ITEMS.items()}


def pooled(src):
    return {i: {"perTicket": float(src[f"{i}_units"].sum() / src.tickets_sold.sum()),
                "paid": float(src[f"{i}_gross"].sum() / src[f"{i}_units"].sum())} for i in ITEM_ORDER}


last = m.groupby("performer_id").last()
notes = {"E111": "evening adjustment from P25", "E155": "matinee adjustment from P25"}
data = {
    "items": [{"key": i, "name": name_of[i]} for i in ITEM_ORDER],
    "menu": {i: float(env["PRICE_NOW"][i]) for i in ITEM_ORDER},
    "elasticity": env["ELASTICITY"],
    "dayVsEvening": {i: float(v) for i, v in env["DAY_VS_EVENING"].items()},
    "groups": GROUPS,
    "groupBasis": {g: pooled(m[m.group == g]) for g in GROUPS},
    "groupStats": {g: {"shows": int((m.group == g).sum()),
                       "alc": round(float(m[m.group == g].alc_gross_pc.mean()), 1),
                       "spend": round(float(m[m.group == g].conc_gross_pc.mean()), 1)} for g in GROUPS},
    "defaultCard": {g: {i: float(CARD.loc[i, g]) for i in ITEM_ORDER} for g in GROUPS},
    "history": [{
        "e": r.event_id, "p": r.performer_id, "type": r.event_type, "genre": r.genre, "day": r.day_of_week,
        "time": r.time_of_day, "tickets": int(r.tickets_sold), "group": r.group,
        "alc": round(float(r.alc_gross_pc), 2), "oth": round(float(r.food_gross_pc + r.nabev_gross_pc), 2),
        "spend": round(float(r.conc_gross_pc), 2),
        "items": {i: [int(r[f"{i}_units"]), round(float(r[f"{i}_gross"]), 2)] for i in ITEM_ORDER},
    } for _, r in m.iterrows()],
    "upcoming": [],
    "historicalGroups": [{"e": r.event_id, "group": r.group} for _, r in m.iterrows()],
}
for _, s in up.iterrows():
    own = s.performer_id in last.index
    b = env["basis"](s)
    data["upcoming"].append({
        "e": s.event_id, "p": s.performer_id, "type": s.event_type, "genre": s.genre, "day": s.day_of_week,
        "time": s.time_of_day, "toDate": int(s.tickets_sold_to_date), "group": s.group,
        "basis": "own" if own else "group", "note": notes.get(s.event_id, ""),
        "lastVisit": f"{last.loc[s.performer_id, 'event_id']}, {int(last.loc[s.performer_id, 'tickets_sold']):,} fans" if own else "First visit",
        "att": {k: int(round(s[f"att_{k}"])) for k in ["low", "base", "high"]},
        "items": {i: {"perTicket": float(b[i][0]), "paid": float(b[i][1])} for i in ITEM_ORDER},
    })
json.dump(data, open("data.json", "w"), separators=(",", ":"))
print("wrote data.json:", len(data["history"]), "past shows,", len(data["upcoming"]), "upcoming shows")
