#!/usr/bin/env python3
"""Copy the study's figures into calculator/data.js, so the page runs on the same
numbers as arithmetic.py. Run after any change to arithmetic.py or figures.py:
    python3 calculator/export_data.py
"""
import contextlib
import io
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))
with contextlib.redirect_stdout(io.StringIO()):
    import arithmetic as ar

# Program limits live in figures.py beside Figure 6.1. Read them as text, so this
# script does not need matplotlib.
src = (ROOT / "figures.py").read_text(encoding="utf-8")
def limit(name):
    return int(re.search(rf"^{name}\s*=\s*(\d+)", src, re.M).group(1))

# Medigap Plan G, men, all other Texas ZIP codes: the same WPS 2026 filing as
# ar.PLAN_G (src/arith/wps-2026-medigap-tx.pdf, MALE table, Plan G column).
PLAN_G_MEN = {65: 2224.44, 66: 2303.64, 67: 2382.84, 68: 2476.92, 69: 2570.88,
              70: 2664.96, 71: 2759.04}

_, items = ar.budget(ar.AVG_RETIRED)
def item(prefix):
    return next(v for k, v in items.items() if k.startswith(prefix))

data = {
    "costGrowth": ar.COST_GROWTH,
    "cola": ar.COLA,
    "savings": ar.SAVINGS,
    "benefits": {"average": ar.AVG_RETIRED, "widow": ar.AVG_WIDOW, "maximum": ar.MAX_AT_62},
    "defaults": {
        "rent": item("Rent"),
        "carPayment": item("Car payment"),
        "carRunning": item("Car insurance") + item("Gasoline") + item("Car maintenance"),
        "food": item("Food at home"),
        "phone": item("Phone") + item("Internet"),
        "outOfPocket": item("Doctor"),
        "other": item("Clothing") + item("Personal care") + item("Household supplies"),
    },
    "aca": {"bench40": ar.BENCH_40, "age62": ar.AGE_62, "age40": ar.AGE_40,
            "fpl": ar.FPL_2025, "bands": ar.BANDS},
    "medicare": {"month": ar.MEDICARE_MONTH, "partB": ar.MEDICARE["Part B"],
                 "partD": ar.MEDICARE["Part D base premium"]},
    "planG": {"women": ar.PLAN_G, "men": PLAN_G_MEN},
    "car": {"loanMonths": ar.LOAN_MONTHS, "replaceMonth": ar.REPLACE_MONTH},
    "snap": {"fy26": [ar.SNAP_NET_LIMIT, ar.SNAP_STD, ar.SNAP_MIN, ar.SNAP_MAX],
             "fy27": list(ar.SNAP_FY27), "medFloor": ar.SNAP_MED_FLOOR},
    "limits": {"extraHelp": limit("EXTRA_HELP"), "qi": limit("QI_LIMIT"),
               "ceapYear": limit("CEAP_YEAR"), "tefapYear": limit("TEFAP_YEAR")},
}

out = HERE / "data.js"
out.write_text("// Written by export_data.py from arithmetic.py and figures.py. Do not edit.\n"
               "window.RUNOUT = " + json.dumps(data, indent=1) + ";\n", encoding="utf-8")
print(f"wrote {out}")
