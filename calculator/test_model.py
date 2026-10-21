#!/usr/bin/env python3
"""Check the page's arithmetic (model.js on data.js) against arithmetic.py and
Chapter 6, to the dollar. Needs node. Run: python3 calculator/test_model.py
"""
import contextlib
import io
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
with contextlib.redirect_stdout(io.StringIO()):
    import arithmetic as ar

JS = r"""
const fs = require("fs"), vm = require("vm");
const ctx = { window: {} }; vm.createContext(ctx);
vm.runInContext(fs.readFileSync(process.argv[1] + "/data.js", "utf8"), ctx);
const D = ctx.window.RUNOUT, M = require(process.argv[1] + "/model.js");
const cases = JSON.parse(process.argv[2]);
const out = cases.map(([benefit, savings]) => {
  const v = Object.assign({ benefit, savings, sex: "women" }, D.defaults);
  const r = M.run(v, D);
  return { out: r.out, balance: r.rows[9].balance, firstGap: r.firstGap, programs: M.programs(v, D) };
});
console.log(JSON.stringify(out));
"""

cases = [(b, s) for _, b, s in ar.CASES]
page = json.loads(subprocess.run(["node", "-e", JS, str(HERE), json.dumps(cases)],
                                 capture_output=True, text=True, check=True).stdout)

failed = 0
def check(label, got, want, tol=1.0):
    global failed
    ok = (got is None and want is None) or (got is not None and want is not None and abs(got - want) < tol)
    failed += not ok
    print(f"  {'ok  ' if ok else 'FAIL'} {label}: page {got}, study {want}")

for (label, b, s), p in zip(ar.CASES, page):
    with contextlib.redirect_stdout(io.StringIO()):
        out, bal, gap0 = ar.run(label, b, s)
    print(label)
    check("runs out at", p["out"], out, 0.5)
    check("savings at 71", round(p["balance"]), round(bal))
    check("first-month gap", round(p["firstGap"]), round(gap0))

# Chapter 6: the average retiree against each program
print("Chapter 6, average retiree")
pr = page[1]["programs"]
check("SNAP a month", pr["snap"]["amount"], 25)
check("Extra Help, over by", round(pr["extraHelp"]["over"]), 56)
check("Medicare premium help, over by", round(pr["qi"]["over"]), 255)
check("utility help, over by", round(pr["ceap"]["over"]), 76)
check("food bank, under by", round(-pr["tefap"]["over"] * 12), 4674)

print("PASS" if not failed else f"{failed} FAILED")
sys.exit(1 if failed else 0)
