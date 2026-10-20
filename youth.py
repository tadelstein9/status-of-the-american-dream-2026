#!/usr/bin/env python3
"""A 25-year-old man without a degree starts a household in 2026. Can he pay for it?

Every input names its file in src/youth/raw/. Run: python3 youth.py
"""

PAY = 51430          # Census PINC-03, 2025 earnings: men 25-34, high school graduates, worked
                     # full time year round (src/youth/raw/pinc03/pinc03_2_5_2_1.xlsx, median).
                     # Replaces Pew's $45,000, which counted 2022 dollars (y01), on the author's decision, 19 Oct 2026.
STD_SINGLE = 16100   # IRS Rev. Proc. 2025-32, sec. 4.14(1) (y15, p. 18)
STD_HOH = 24150      # same section, head of household
PAYROLL = 0.0765     # 26 U.S.C. 3101: 6.2% Social Security + 1.45% Medicare

def federal_tax_single(income):
    """2026 single brackets, IRS Rev. Proc. 2025-32 Table 3 (y15, p. 11); valid to $50,400 taxable."""
    t = max(0, income - STD_SINGLE)
    assert t <= 50400, "extend the brackets"
    return 0.10 * t if t <= 12400 else 1240 + 0.12 * (t - 12400)

def federal_tax_hoh(income):
    """2026 head-of-household brackets, Rev. Proc. 2025-32 Table 2 (y15, pp. 10-11)."""
    t = max(0, income - STD_HOH)
    assert t <= 67450, "extend the brackets"
    return 0.10 * t if t <= 17700 else 1770 + 0.12 * (t - 17700)

def credits_one_child(income, tax):
    """Federal credits for a parent of one child, 2026. Returns (tax after credits, refund).
    Child tax credit $2,200, refundable up to $1,700 at 15% of earnings over $2,500
    (Rev. Proc. 2025-32 sec. 4.05, y15 p. 14; 26 USC 24(d), (h)(6), gaps-b/b05).
    Child care credit: 35% of up to $3,000 at this income, non-refundable (26 USC 21,
    gaps-b/b03; IRS, gaps-b/b04). EITC one child: max $4,427, phase-out $23,890-$51,593
    (y15 sec. 4.06(1), p. 15)."""
    ctc_used = min(2200, tax)
    tax -= ctc_used
    refund = min(1700, 2200 - ctc_used, 0.15 * max(0, income - 2500))
    tax -= min(tax, 0.35 * 3000)
    if income <= 23890:
        eitc = 4427
    else:
        eitc = max(0, 4427 * (51593 - income) / (51593 - 23890))
    return tax, refund + eitc

TAKE_HOME = (PAY - federal_tax_single(PAY) - PAYROLL * PAY) / 12   # no state income tax, as in Texas
_tax_hoh, _refund = credits_one_child(PAY, federal_tax_hoh(PAY))
TAKE_HOME_FATHER = (PAY - _tax_hoh + _refund - PAYROLL * PAY) / 12   # head of household, credits counted

# Health insurance: benchmark silver at 25 after the 2026 credit.
FPL = 15650                       # HHS 2025 guidelines, used for 2026 coverage (y14, p. 5917)
pct = PAY / FPL * 100             # percent of the poverty guideline
# Rev. Proc. 2025-25 applicable percentage (y10, p. 3): 8.44%-9.96% across 250-300%,
# flat 9.96% from 300% to 400%.
applicable = 0.0844 + (min(pct, 300) - 250) / 50 * (0.0996 - 0.0844) if pct < 300 else 0.0996
BENCH_25 = 625 * 1.004 / 1.278    # KFF 2026 benchmark at 40; CMS default curve 25 vs 40 (y13, p. 1)
HEALTH = min(BENCH_25, applicable * PAY / 12)

FOOD_MAN, FOOD_CHILD = 319.00, 114.20   # USDA Thrifty plan, Sep 2026, male 20-50, child age 1 (y16, p. 1)

def budget(rent, childcare_year, child=True):
    food = (FOOD_MAN + FOOD_CHILD) * 1.10 if child else FOOD_MAN * 1.20   # USDA household-size adjustment
    return {
        "Rent with utilities (HUD Fair Market Rent via NLIHC)": rent,
        "Deposit spread over a year (Zillow 2025 typical, $795)": 795 / 12,
        "Car payment, used (Experian Q2 2026)": 542,
        "Car insurance (BLS CE 2024, households 25-34)": 1888 / 12,
        "Food (USDA Thrifty plan)": food,
        "Infant care in a center (Child Care Aware 2025)": childcare_year / 12 if child else 0,
        "Phone (BLS CE 2024, households 25-34)": 1221 / 12,
        "Internet (BLS CE 2024, all households, $697.90/yr)": 697.90 / 12,
        "Health insurance, his own benchmark plan after credit": HEALTH,
    }

CASES = [
    ("Father of one, national: two-bedroom $1,806, infant care $15,636", 1806, 15636, True),
    ("Father of one, Texas: two-bedroom $1,557, infant care $10,894", 1557, 10894, True),
    ("Alone, national: one-bedroom $1,518, no child", 1518, 0, False),
]

if __name__ == "__main__":
    print(f"Pay ${PAY:,}; federal tax ${federal_tax_single(PAY):,.0f}; payroll ${PAYROLL*PAY:,.0f}; "
          f"take-home ${TAKE_HOME:,.0f}/month")
    print(f"Health: {pct:.1f}% of poverty, pays {applicable:.2%} of income = ${HEALTH:,.0f}/month "
          f"(benchmark ${BENCH_25:,.0f})")
    print(f"Father, head of household: tax ${_tax_hoh:,.0f} after credits, refund ${_refund:,.0f} "
          f"(EITC + refundable child credit); take-home ${TAKE_HOME_FATHER:,.0f}/month")
    for label, rent, care, child in CASES:
        b = budget(rent, care, child)
        total = sum(b.values())
        home = TAKE_HOME_FATHER if child else TAKE_HOME
        print(f"\n== {label} ==")
        for k, v in b.items():
            if v:
                print(f"  {k:58} ${v:7,.0f}")
        gap = total - home
        print(f"  {'Total':58} ${total:7,.0f}  = {total / home:.0%} of take-home "
              f"({'short' if gap > 0 else 'left over'} ${abs(gap):,.0f}/month)")
    print("\nNot yet counted: the infant's health coverage (over Texas Medicaid's $3,571 and CHIP's "
          "$3,625 monthly limits for two, gaps-b/b01) and a family marketplace plan.")
