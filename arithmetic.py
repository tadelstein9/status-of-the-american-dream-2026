#!/usr/bin/env python3
"""A single renter retires at 62 in 2026 on Social Security. Does the money last?

Every input names its source in src/ or src/arith/. Household figures from the
BLS Consumer Expenditure Survey (CE) are divided by the household's people or
vehicles, as marked. Run: python3 arithmetic.py
"""

# Income, monthly (SSA)
MAX_AT_62 = 2969      # src/arith/ssa-oact-maximum-benefit.txt, 2026 row, age 62
AVG_RETIRED = 2071    # src/arith/ssa-2026-cola-factsheet.txt, all retired workers, Jan 2026
EARNINGS_TEST = 24480 # same fact sheet: under full retirement age, $1 withheld per $2 above this

# CE 2024, ages 55-64 (src/arith/bls-ce-reference-person-age-ranges-2024.csv)
CE_PEOPLE, CE_VEHICLES = 2.2, 2.1

def per_vehicle(annual): return annual / CE_VEHICLES / 12
def per_person(annual): return annual / CE_PEOPLE / 12

# Health insurance at 62, before Medicare at 65
BENCH_40 = 625                    # KFF 2026 U.S. average benchmark silver, age 40 (secondary report)
AGE_62, AGE_40 = 2.873, 1.278     # src/arith/cms-age-curve-2016.pdf, p. 4, federal default curve
FPL_2025 = 15650                  # poverty line used for 2026 coverage
# Rev. Proc. 2025-25 applicable percentages for 2026 (secondary reports agree):
# (from % of poverty line, to %, share of income at start, at end)
BANDS = [(100, 133, 0.0210, 0.0210), (133, 150, 0.0314, 0.0419), (150, 200, 0.0419, 0.0660),
         (200, 250, 0.0660, 0.0844), (250, 300, 0.0844, 0.0996), (300, 400, 0.0996, 0.0996)]

def applicable_pct(pct_fpl):
    for lo, hi, a, b in BANDS:
        if lo <= pct_fpl < hi:
            return a + (pct_fpl - lo) / (hi - lo) * (b - a)
    return None                               # no credit below 100% or at 400% and above

def premium_after_credit(monthly_benefit):
    full = BENCH_40 * AGE_62 / AGE_40
    income = monthly_benefit * 12             # all Social Security counts toward ACA income
    pct = applicable_pct(income / FPL_2025 * 100)
    if pct is None:
        return full, None
    return full, min(full, pct * income / 12)

def budget(monthly_benefit):
    full, net = premium_after_credit(monthly_benefit)
    return full, {
        "Rent, with utilities (Census ACS 2024 median gross rent)": 1487,
        "Car payment, used car (Experian Q2 2026)": 542,
        "Car insurance (CE, per vehicle)": per_vehicle(2252),
        "Gasoline (CE, per vehicle)": per_vehicle(2522),
        "Car maintenance (CE, per vehicle)": per_vehicle(1154),
        "Food at home (USDA low-cost plan, woman 51-70, Sep 2026)": 268.90,   # src/youth/raw/y16-usda-cost-of-food-sep2026-LowModLib.pdf
        "Phone (CE telephone services, per person)": per_person(1596),
        "Health insurance, benchmark silver after tax credit": net if net is not None else full,
        "Doctor, drugs, supplies out of pocket (CE, per person)": per_person(1352 + 794 + 252),
        "Clothing (CE, per person)": per_person(2032),
        "Personal care (CE, per person)": per_person(1023),
        "Household supplies (CE, per person)": per_person(1022),
        "Internet (BLS CE 2024, all households, $697.90/yr; src/gaps-b/b07)": 697.90 / 12,
    }

# Ten years of prices. BLS R-CPI-E (Americans 62+) averaged 2.73% a year 2010-2024
# (235.008 -> 342.483); CPI-W, which sets Social Security's COLA, averaged 2.63%
# (213.967 -> 307.552). src/primary/04-bls-r-cpi-e-data.xlsx, Table 2, annual average;
# src/primary/04b-bls-cpi-w-cw.data.1.AllItems.txt, CWUR0000SA0 M13. BLS calls R-CPI-E
# a research index whose conclusions "should be treated as tentative." The Senior
# Citizens League's 4.9%/3.9% (src/09) is its own market basket, not a BLS index.
COST_GROWTH, COLA = 0.0273, 0.0263
SAVINGS = 86900   # median retirement account, families that have one (src/21, p. 21)

CAR = "Car payment, used car (Experian Q2 2026)"
HEALTH = "Health insurance, benchmark silver after tax credit"
LOAN_MONTHS = 67.7     # average used-car loan term, Experian Q1 2026 (secondary report)
# Replacement car. A used car at $15,000-$20,000 averaged 6 years old (Edmunds Q2 2026,
# src/arith/edmunds-q2-2026-used.txt). The average U.S. vehicle on the road is 12.8 years
# old (S&P Global Mobility 2025, src/arith/sp-2025-vehicle-age-aapex.txt). Assume the
# car is replaced when it reaches that age, with a new loan at the same terms, priced up
# by retiree inflation.
CAR_AGE_AT_PURCHASE, CAR_AGE_AT_REPLACEMENT = 6, 12.8
REPLACE_MONTH = round((CAR_AGE_AT_REPLACEMENT - CAR_AGE_AT_PURCHASE) * 12)

MEDICARE_MONTH = 36    # retires at 62, Medicare at 65
MEDICARE = {           # 2026 dollars, monthly
    "Part B": 202.90,          # CMS 2026 fact sheet
    "Part D base premium": 38.99,  # CMS 2026 base beneficiary premium (secondary report)
}
# Medigap Plan G, annual premium by age, WPS 2026 Texas outline of coverage, FEMALE table,
# all other Texas ZIP codes (src/arith/wps-2026-medigap-tx.pdf), since the worked retirees
# are women. (The male table, used before 19 Oct 2026, ran $2,224.44 at 65.) Texas prices by
# attained age. Check: KFF puts the 2025 U.S. average for current policyholders at $194
# a month (src/arith/kff-medigap-key-facts.txt).
PLAN_G = {65: 2022.12, 66: 2094.24, 67: 2166.36, 68: 2251.68, 69: 2337.12,
          70: 2422.68, 71: 2508.12}

def car_payment(items, m):
    if m < LOAN_MONTHS:
        return items[CAR]
    if REPLACE_MONTH <= m < REPLACE_MONTH + LOAN_MONTHS:
        return items[CAR] * (1 + COST_GROWTH) ** (REPLACE_MONTH // 12)
    return 0

def month_cost(items, m):
    """Cost in month m (0 = first month at 62). A loan payment is fixed for its term;
    everything else rises with retiree prices."""
    grow = (1 + COST_GROWTH) ** (m // 12)
    other = sum(v for k, v in items.items() if k not in (CAR, HEALTH))
    if m >= MEDICARE_MONTH:
        health = sum(MEDICARE.values()) + PLAN_G[62 + m // 12] / 12
    else:
        health = items[HEALTH]
    return (other + health) * grow + car_payment(items, m)

RENT = "Rent, with utilities (Census ACS 2024 median gross rent)"
OOP = "Doctor, drugs, supplies out of pocket (CE, per person)"

# SNAP (EBT) for a one-person household, Texas, FY2026: src/assist/texas-hhsc-bulletin-25-15
# -snap-fy2026.pdf. Net income limit $1,305; standard deduction $209; minimum benefit $24.
# A household with a member 60 or older skips the gross income test, deducts medical costs
# above $35 a month, and has no cap on the shelter deduction; the maximum benefit for one
# person is $298 (USDA FY2026 memo, src/primary/01-fns-snap-cola-fy26-memo.pdf; elderly rules
# 7 CFR 273.9, src/primary/01c). From October 2026 the FY2027 amounts apply: net limit $1,330,
# standard deduction $217, minimum $25, maximum $306 (src/primary/01e-fna-snap-cola-fy27-memo.pdf).
# Later fiscal years: FY2027 amounts raised by COLA each October.
SNAP_NET_LIMIT, SNAP_STD, SNAP_MIN, SNAP_MAX, SNAP_MED_FLOOR = 1305, 209, 24, 298, 35
SNAP_FY27 = (1330, 217, 25, 306)

def snap_params(m):
    """SNAP amounts for model month m (0 = January 2026). Fiscal years begin in October."""
    fy = (m + 3) // 12          # 0 = FY2026 (Jan-Sep 2026), 1 = FY2027 (Oct 2026-Sep 2027), ...
    if fy == 0:
        return SNAP_NET_LIMIT, SNAP_STD, SNAP_MIN, SNAP_MAX
    k = (1 + COLA) ** (fy - 1)
    lim, std, mn, mx = SNAP_FY27
    return lim * k, std * k, mn, mx * k

def snap(items, m, income):
    grow = (1 + COST_GROWTH) ** (m // 12)
    lim, std, mn, mx = snap_params(m)
    health = (sum(MEDICARE.values()) + PLAN_G[62 + m // 12] / 12) if m >= MEDICARE_MONTH else items[HEALTH]
    medical = max(0, (health + items[OOP]) * grow - SNAP_MED_FLOOR)
    adjusted = max(0, income - std - medical)
    shelter = max(0, items[RENT] * grow - adjusted / 2)
    net = max(0, adjusted - shelter)
    if net > lim:
        return 0
    return max(mn, mx - 0.3 * net)

def run(label, benefit, savings=SAVINGS):
    """Print one worked case; return (age the money runs out or None, savings left at 71)."""
    full, items = budget(benefit)
    cost = sum(items.values())
    print(f"\n== {label}: ${benefit:,}/month ==")
    for k, v in items.items():
        print(f"  {k:62} ${v:8,.0f}")
    print(f"  {'Total, first month':62} ${cost:8,.0f}")
    print(f"  (health insurance before the credit: ${full:,.0f})")
    print(f"  From 65, Medicare replaces it: ${sum(MEDICARE.values()) + PLAN_G[65] / 12:,.0f}/month"
          f" at 65, ${sum(MEDICARE.values()) + PLAN_G[71] / 12:,.0f} at 71, in 2026 prices")
    print(f"  Car loan ends after month {LOAN_MONTHS}; replacement car bought in month {REPLACE_MONTH}"
          f" (age {62 + REPLACE_MONTH // 12}), payment ${car_payment(items, REPLACE_MONTH):,.0f}")
    print(f"  Monthly gap: ${benefit - cost:+,.0f}")
    bal, out = savings, None
    print(f"  Year  age  benefit/mo  SNAP/mo  costs/mo   gap/yr     savings left (start ${savings:,})")
    for y in range(10):
        b = benefit * (1 + COLA) ** y
        costs = [month_cost(items, y * 12 + m) for m in range(12)]
        food = [snap(items, y * 12 + m, b) for m in range(12)]
        gap = b * 12 + sum(food) - sum(costs)
        bal += gap
        if out is None and bal < 0:
            out = 62 + y
        print(f"  {y+1:>4}  {62+y:>3}  ${b:9,.0f}  ${sum(food)/12:6,.0f}  ${sum(costs)/12:8,.0f}"
              f"  ${gap:+9,.0f}  ${bal:+12,.0f}")
    return out, bal, benefit - cost

# The worked cases. Each person rents alone at the median rent, drives a used car on a
# loan, and starts at 62 in 2026. Only the benefit and the savings change.
AVG_WIDOW = 1919      # src/arith/ssa-2026-cola-factsheet.txt, aged widow(er) alone, Jan 2026
CASES = [
    ("The top earner: maximum benefit, median savings", MAX_AT_62, SAVINGS),
    ("The average retiree: average benefit, median savings", AVG_RETIRED, SAVINGS),
    ("The widow: average survivor's benefit, median savings", AVG_WIDOW, SAVINGS),
    ("The average retiree with no retirement account (46% of families)", AVG_RETIRED, 0),
]

if __name__ == "__main__":
    summary = [(label, b, s, *run(label, b, s)) for label, b, s in CASES]
    print("\n== The worked cases, side by side ==")
    for label, b, s, out, left, gap0 in summary:
        when = f"runs out at {out}" if out else f"${left:,.0f} left at 71"
        print(f"  {label:66} ${b:,}/mo  first-month gap ${gap0:+,.0f}  {when}")
    print(f"\nWork before full retirement age: SSA withholds $1 for every $2 earned above ${EARNINGS_TEST:,} a year.")
