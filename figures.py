#!/usr/bin/env python3
"""Draw the study's figures from its own scripts, so a figure redraws when a number changes.

Run: .venv/bin/python figures.py   ->  figures/*.png and figures/*.svg  (needs matplotlib, openpyxl, xlrd)
Palette: the dataviz reference categorical order (validated light, 6 slots).
"""
import os
import sys
import textwrap

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import arithmetic as ar  # noqa: E402
import youth as yo       # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "figures")
SURFACE, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#6250d6"]

K = 1.4  # type scale: a figure shrinks to a ~680 px column on Substack

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 10 * K, "axes.edgecolor": GRID,
    "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
})


def save(fig, name):
    # Wrap titles and notes to the figure's width, so a long note never widens the image
    # and shrinks the chart when Substack fits it to its column.
    for ax in fig.axes:
        for title in (ax.title, ax._left_title, ax._right_title):
            title.set_text(textwrap.fill(title.get_text(), 62))
        labels = [t.get_text() for t in ax.get_yticklabels()]
        if any(len(t) > 24 for t in labels):  # long row labels widen a bar chart
            ax.set_yticks(ax.get_yticks(), [textwrap.fill(t, 24) for t in labels])
    for t in fig.texts:
        t.set_text(textwrap.fill(" ".join(t.get_text().split()), 112))
    os.makedirs(OUT, exist_ok=True)
    for ext in ("png", "svg"):
        fig.savefig(os.path.join(OUT, f"{name}.{ext}"), dpi=200, bbox_inches="tight")
    plt.close(fig)


def money(n):
    return f"${n:,.0f}"


def fig_ledger():
    """Figure 2.1: the young father's monthly bills against his take-home pay."""
    groups = [
        ("Rent and deposit", lambda b: b["Rent with utilities (HUD Fair Market Rent via NLIHC)"]
         + b["Deposit spread over a year (Zillow 2025 typical, $795)"]),
        ("Infant care", lambda b: b["Infant care in a center (Child Care Aware 2025)"]),
        ("Car, insurance", lambda b: b["Car payment, used (Experian Q2 2026)"]
         + b["Car insurance (BLS CE 2024, households 25-34)"]),
        ("Food", lambda b: b["Food (USDA Thrifty plan)"]),
        ("His health plan", lambda b: b["Health insurance, his own benchmark plan after credit"]),
        ("Phone, internet", lambda b: b["Phone (BLS CE 2024, households 25-34)"]
         + b["Internet (BLS CE 2024, all households, $697.90/yr)"]),
    ]
    rows = [("United States", yo.budget(1806, 15636, True)), ("Texas", yo.budget(1557, 10894, True))]
    fig, ax = plt.subplots(figsize=(8.5, 3.6))
    for i, (label, b) in enumerate(rows):
        left = 0
        for j, (name, f) in enumerate(groups):
            v = f(b)
            ax.barh(i, v - 2, left=left, color=SERIES[j], height=0.55)  # 2px-style gap between fills
            if v > 900:
                ax.text(left + v / 2, i, f"{name}\n{money(v)}", ha="center", va="center",
                        fontsize=8 * K, color=INK)
            left += v
        ax.text(left + 40, i, f"{money(left)}\n{left / yo.TAKE_HOME_FATHER:.0%} of pay",
                va="center", fontsize=9 * K, color=INK, fontweight="bold")
    ax.axvline(yo.TAKE_HOME_FATHER, color=INK, lw=2)
    ax.text(yo.TAKE_HOME_FATHER - 40, -0.42, f"Take-home pay {money(yo.TAKE_HOME_FATHER)}",
            ha="right", va="bottom", fontsize=9 * K, color=INK)
    from matplotlib.patches import Patch
    us = rows[0][1]
    ax.legend(handles=[Patch(color=SERIES[j], label=f"{n} ({money(f(us))} US)") for j, (n, f) in enumerate(groups)],
              loc="upper center", bbox_to_anchor=(0.45, -0.13), ncol=3, frameon=False, fontsize=8 * K)
    ax.set_yticks(range(len(rows)), [r[0] for r in rows])
    ax.set_ylim(-0.55, 1.45)
    ax.invert_yaxis()
    ax.set_xlim(0, 5800)
    ax.xaxis.set_major_formatter(lambda x, _: money(x))
    ax.grid(axis="x", color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.set_title("Figure 2.1. A young father's monthly bills against his take-home pay, 2026",
                 loc="left", fontsize=11 * K, color=INK, pad=22)
    fig.text(0.01, -0.2, "Man 25–34, high school graduate, full time, $51,430 (Census PINC-03, 2025); head of household "
             "with one infant; federal credits counted.\nSources: NLIHC; Zillow; Child Care Aware; Experian; BLS CE 2024; USDA; "
             "KFF/CMS/IRS. The infant's health coverage is not counted. Computed by youth.py.",
             fontsize=7.5 * K, color=INK2, ha="left", va="top")
    save(fig, "fig-2-1-young-fathers-ledger")


def balances(benefit, savings):
    full, items = ar.budget(benefit)
    bal, out = savings, [savings]
    for y in range(10):
        b = benefit * (1 + ar.COLA) ** y
        costs = sum(ar.month_cost(items, y * 12 + m) for m in range(12))
        food = sum(ar.snap(items, y * 12 + m, b) for m in range(12))
        bal += b * 12 + food - costs
        out.append(bal)
    return out


def fig_runout():
    """Figure 5.1: savings by age for the four worked retiree cases."""
    labels = ["Top earner", "Average retiree", "Widow", "No retirement account"]
    fig, ax = plt.subplots(figsize=(8.5, 4.4))
    ages = list(range(62, 73))
    for i, ((_, benefit, savings), name) in enumerate(zip(ar.CASES, labels)):
        bal = balances(benefit, savings)
        ax.plot(ages, bal, color=SERIES[i], lw=2, marker="o", ms=4)
        nudge = {1: 9000, 2: -9000}.get(i, 0)
        ax.text(72.15, bal[-1] + nudge, f"{name}\n({money(benefit)}/mo)", va="center", fontsize=8 * K, color=INK)
        for a0, a1, v0, v1 in zip(ages, ages[1:], bal, bal[1:]):
            if v0 >= 0 > v1 or (v0 == 0 and v1 < 0):
                x = a0 + v0 / (v0 - v1)
                ax.plot([x], [0], marker="o", ms=8, color=SERIES[i], mec=SURFACE, mew=2, zorder=5)
                pos = {1: (x + 0.35, 22000), 2: (x - 0.5, -26000), 3: (x + 0.4, 14000)}[i]
                ax.annotate(f"runs out at {int(x)}", (x, 0), xytext=pos, fontsize=8 * K, color=INK,
                            ha="left" if pos[0] > x else "right",
                            arrowprops=dict(arrowstyle="-", color=INK2, lw=0.8))
    ax.axhline(0, color=INK, lw=1.2)
    ax.set_xlim(62, 74.6)
    ax.set_xticks(ages)
    ax.set_xlabel("Age (start of year)")
    ax.set_ylabel("Savings left (below zero: running shortfall)")
    ax.yaxis.set_major_formatter(lambda y, _: ("−" if y < 0 else "") + money(abs(y)))
    ax.grid(axis="y", color=GRID, lw=0.8)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.set_title("Figure 5.1. Retirement savings by age for four people who retire at 62 in 2026",
                 loc="left", fontsize=11 * K, color=INK, pad=10)
    fig.text(0.01, -0.03, "Each rents alone at the median rent and drives a used car on a loan; median retirement savings "
             "$86,900 except the last case. Medicare at 65; car replaced at 68;\nTexas SNAP counted. Prices rise 2.73% a year "
             "(BLS R-CPI-E), benefits 2.63% (CPI-W). Sources in sources.md. Computed by arithmetic.py.",
             fontsize=7.5 * K, color=INK2, ha="left", va="top")
    save(fig, "fig-5-1-retirement-run-out")


def tidy(ax, grid="x"):
    ax.grid(axis=grid, color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    for s in ("top", "right", "left" if grid == "x" else "bottom"):
        ax.spines[s].set_visible(False)


def note(fig, text, y=-0.06):
    fig.text(0.01, y, text, fontsize=7.5 * K, color=INK2, ha="left", va="top")


POVERTY_GUIDELINE_ONE = 15960  # HHS 2026, one person (sources.md; Chapter 6)


def fig_thesis():
    """Figure T: what each worked case brings in against what a plain life costs, a month."""
    father = sum(yo.budget(1806, 15636, True).values())
    _, items = ar.budget(ar.AVG_RETIRED)
    retiree = sum(items.values())
    groups = [("Young father, 25\nwith one infant", yo.TAKE_HOME_FATHER, father, "pay"),
              ("Average retiree, 62\nliving alone", ar.AVG_RETIRED, retiree, "check")]
    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    for i, (name, inc, cost, inc_label) in enumerate(groups):
        x = i * 3
        ax.bar(x, inc, width=0.9, color=SERIES[0])
        ax.bar(x + 1, cost, width=0.9, color=SERIES[1])
        ax.text(x, inc - 120, f"{money(inc)}\n{inc_label}", ha="center", va="top", fontsize=9 * K, color="white",
                fontweight="bold")
        ax.text(x + 1, cost - 120, f"{money(cost)}\nplain life", ha="center", va="top", fontsize=9 * K,
                color="white", fontweight="bold")
        ax.text(x + 0.5, cost + 150, f"Short {money(cost - inc)} a month", ha="center", va="bottom",
                fontsize=10 * K, color=INK, fontweight="bold")
    line = POVERTY_GUIDELINE_ONE / 12
    ax.plot([2.45, 4.55], [line, line], color=INK, lw=1.5, ls="--")
    ax.text(4.65, line, f"Poverty line,\none person:\n{money(line)}", ha="left", va="center",
            fontsize=8.5 * K, color=INK)
    ax.set_xticks([0.5, 3.5], [g[0] for g in groups])
    ax.tick_params(axis="x", length=0)
    ax.set_xlim(-0.7, 5.9)
    ax.set_ylim(0, 5800)
    ax.yaxis.set_major_formatter(lambda v, _: money(v))
    tidy(ax, "y")
    ax.set_title("Figure T. Both bring in more than the poverty line and less than a plain life costs, a month, 2026",
                 loc="left", fontsize=11 * K, color=INK, pad=10)
    note(fig, "Plain life: the worked cases' monthly costs for rent, food, a car, health coverage, phone and internet, "
         "and for the father, infant care. Sources in the chapters; computed by youth.py (Chapter 2) and "
         "arithmetic.py (Chapter 5).", y=-0.02)
    save(fig, "fig-T-thesis-gap")


def fig_line():
    """Figure 1.1: the poverty line, the Elder Index and the average Social Security check, one person, a year."""
    rows = [  # (label, dollars a year, source year)
        ("Census poverty threshold, one person 65+ (2025)", 15440),
        ("HHS poverty guideline, one person (2026)", 15960),
        ("Average retired worker's Social Security (2026)", ar.AVG_RETIRED * 12),
        ("Elder Index, single renter in good health (2025)", 34032),  # src/primary/07d, Table 1, p. 4
    ]
    fig, ax = plt.subplots(figsize=(8.5, 4.2))
    for i, (label, v) in enumerate(rows):
        ax.barh(i, v, height=0.55, color=SERIES[2] if i == 2 else SERIES[0] if i < 2 else SERIES[1])
        ax.text(v + 300, i, money(v), va="center", fontsize=9 * K, color=INK)
    ax.set_yticks(range(len(rows)), [r[0] for r in rows])
    ax.invert_yaxis()
    ax.set_xlim(0, 38000)
    ax.xaxis.set_major_formatter(lambda x, _: money(x))
    tidy(ax)
    ax.set_title("Figure 1.1. The poverty line, the cost of a plain life and the average Social Security check",
                 loc="left", fontsize=11 * K, color=INK, pad=10)
    note(fig, "Dollars a year, one person. The Elder Index adds up housing, food, transportation, health care and other "
         "basics for an older person.\nSources: Census Bureau, Poverty Thresholds for 2025; Department of Health and Human "
         "Services, 2026 guideline; SSA 2026 fact sheet; Gerontology Institute,\nUniversity of Massachusetts Boston, "
         "\"Living Between the Lines,\" 2026, Table 1.")
    save(fig, "fig-1-1-poverty-line-elder-index")


def fig_price_to_income():
    """Figure 3.1: median home price against median household income (JCHS appendix Table W-16)."""
    import openpyxl
    base = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base, "src/primary/07e-jchs-son-2026-appendix.xlsx")
    if not os.path.exists(path):
        print("Figure 3.1 skipped: download the JCHS 2026 appendix tables to", path)
        return
    ws = openpyxl.load_workbook(path,
                                data_only=True)["W-16"]
    rows = list(ws.iter_rows(min_row=5, max_row=6, values_only=True))
    years, ratio = rows[0][1:], rows[1][1:]
    assert rows[1][0] == "United States"
    fig, ax = plt.subplots(figsize=(8.5, 3.6))
    ax.axhspan(3.1, 3.4, xmin=0, xmax=(2000 - 1989) / (2027 - 1989), color=GRID)
    ax.text(1990.2, 2.7, "1980–1999: between 3.1 and 3.4\n(Hermann, JCHS, 2018)", fontsize=8 * K, color=INK2)
    ax.plot(years, ratio, color=SERIES[0], lw=2)
    for y in (1990, 2005, 2019, 2022, 2025):
        v = ratio[years.index(y)]
        ax.plot([y], [v], marker="o", ms=5, color=SERIES[0])
        ax.text(y, v + 0.12, f"{v:.1f}", ha="center", fontsize=8 * K, color=INK)
    ax.set_xlim(1989, 2027)
    ax.set_ylim(2.5, 5.5)
    ax.set_ylabel("Years of income")
    tidy(ax, "y")
    ax.set_title("Figure 3.1. Median home price against median household income, 1990–2025",
                 loc="left", fontsize=11 * K, color=INK, pad=10)
    note(fig, "Existing single-family homes. 2025 income is a forecast.\nSource: Harvard Joint Center for Housing "
         "Studies, The State of the Nation's Housing 2026, appendix Table W-16 (JCHS tabulations of National Association "
         "of Realtors prices\nand Moody's Analytics income estimates); 1980s range from Alexander Hermann, JCHS Housing "
         "Perspectives, 2018.")
    save(fig, "fig-3-1-price-to-income")


def fig_at_home():
    """Figure 3.2: adults 25-34 living in a parent's home, 1980-2025 (Census AD-1), with first-buyer age (NAR)."""
    import xlrd
    base = os.path.dirname(os.path.abspath(__file__))
    s = xlrd.open_workbook(os.path.join(base, "src/youth/raw/y09b-census-ad1-table.xls")).sheet_by_index(0)
    start = next(i for i in range(s.nrows) if s.cell_value(i, 0) == ".25 to 34 years")
    pts = {}
    for i in range(start + 1, s.nrows):
        label = str(s.cell_value(i, 0))
        if not label.startswith(".."):
            break
        men, women = s.cell_value(i, 3), s.cell_value(i, 7)
        if men == "N":
            continue
        year = int(label[2:6])
        if year not in pts or label.endswith("r"):  # revised rows replace the original
            pts[year] = (men, women)
    years = sorted(y for y in pts if y >= 1980)
    fig, ax = plt.subplots(figsize=(8.5, 3.8))
    for j, name in enumerate(("Men", "Women")):
        v = [pts[y][j] for y in years]
        ax.plot(years, v, color=SERIES[j], lw=2)
        ax.plot([years[0], years[-1]], [v[0], v[-1]], "o", ms=5, color=SERIES[j])
        ax.text(years[0] - 0.6, v[0], f"{v[0]:.1f}%", ha="right", va="center", fontsize=8 * K, color=INK)
        ax.text(years[-1] + 0.6, v[-1], f"{name} {v[-1]:.1f}%", va="center", fontsize=8 * K, color=SERIES[j])
    ax.text(1984, 2.0, "First-time home buyer's median age: late 20s in the 1980s; 40 in 2025",
            fontsize=9 * K, color=INK)
    ax.set_xlim(1977, 2032)
    ax.set_ylim(0, 24)
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:.0f}%")
    ax.set_ylabel("Living in a parent's home")
    tidy(ax, "y")
    ax.set_title("Figure 3.2. Adults 25 to 34 living in a parent's home, 1980–2025",
                 loc="left", fontsize=11 * K, color=INK, pad=10)
    note(fig, "1980 from the decennial census; 1983 on from the Current Population Survey (no data for 1981–1982).\n"
         "Sources: Census Bureau, table AD-1; National Association of Realtors, 2025 Profile of Home Buyers and Sellers, "
         "Highlights, p. 3.")
    save(fig, "fig-3-2-living-at-home")


def fig_messages():
    """Figure 4.2: who writes and who answers on dating sites (sources.md item 60)."""
    rows = [  # (label, percent, shown as)
        ("First messages sent by men", 80, "more than 80%"),
        ("Messages from men that women answer (average)", 20, "under 20%"),
        ("Men who received no message from a woman", 18, "about 18%"),
        ("Women who received no message from a man", 2, "2%"),
    ]
    fig, ax = plt.subplots(figsize=(8.5, 3.0))
    for i, (label, v, shown) in enumerate(rows):
        ax.barh(i, v, height=0.55, color=SERIES[0] if i < 2 else SERIES[1])
        ax.text(v + 1, i, shown, va="center", fontsize=9 * K, color=INK)
    ax.set_yticks(range(len(rows)), [r[0] for r in rows])
    ax.invert_yaxis()
    ax.set_xlim(0, 100)
    ax.xaxis.set_major_formatter(lambda x, _: f"{x:.0f}%")
    tidy(ax)
    ax.set_title("Figure 4.2. Who writes and who answers on dating sites",
                 loc="left", fontsize=11 * K, color=INK, pad=10)
    note(fig, "Top two rows: Bruch and Newman, Science Advances, 2018 (messages on a large dating site in four U.S. cities). "
         "Bottom two rows: Kreager and others,\nJournal of Marriage and Family, 2014 (\"about 18% of men received no "
         "messages from women\"; 98% of women received at least one). Two studies; read each pair on its own.")
    save(fig, "fig-4-2-who-writes")


def fig_degree_dropped():
    """Figure 8.1: what firms did after dropping a degree requirement (HBS and Burning Glass Institute, 2024)."""
    groups = [("Leaders: hired more workers\nwithout degrees", 37, "37%"),
              ("In name only: no change\nin who they hired", 45, "about 45%"),
              ("Backsliders: brief gain,\nthen fewer", 20, "about one-fifth")]
    fig, ax = plt.subplots(figsize=(8.5, 2.4))
    left = 0
    for j, (name, v, shown) in enumerate(groups):
        ax.barh(0, v - 0.5, left=left, height=0.5, color=SERIES[[2, 3, 1][j]])
        ax.text(left + v / 2, 0, shown, ha="center", va="center", fontsize=9 * K, color=INK)
        ax.text(left + v / 2, 0.42, name, ha="center", va="top", fontsize=8 * K, color=INK)
        left += v
    ax.set_xlim(0, 102)
    ax.set_ylim(0.55, -0.4)
    ax.set_yticks([])
    ax.set_xticks([])
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.set_title("Figure 8.1. Firms that dropped a degree requirement: what happened to their hiring",
                 loc="left", fontsize=11 * K, color=INK, pad=10)
    note(fig, "Shares of firms studied, as the report rounds them. Across all firms, the opening \"has borne out in not even "
         "1 in 700 hires last year.\"\nSource: Harvard Business School Project on Managing the Future of Work and Burning "
         "Glass Institute, \"Skills-Based Hiring: The Long Road from Pronouncements to Practice,\" February 2024.", y=0.02)
    save(fig, "fig-8-1-degree-requirements")


def fig_men_per_women():
    """Figure 4.1: never-married men per 100 never-married women, ages 25-34 (Pew 2014, src/02, line 362, 1587)."""
    rows = [("All never-married men", 180, 126), ("Employed never-married men", 139, 91)]
    fig, ax = plt.subplots(figsize=(8.5, 3.0))
    for i, (label, y1960, y2012) in enumerate(rows):
        ax.barh(i - 0.18, y1960, height=0.34, color=SERIES[0])
        ax.barh(i + 0.18, y2012, height=0.34, color=SERIES[1])
        ax.text(y1960 + 3, i - 0.18, f"{y1960} in 1960", va="center", fontsize=9 * K, color=INK)
        ax.text(y2012 + 3, i + 0.18, f"{y2012} in 2012", va="center", fontsize=9 * K, color=INK)
    ax.axvline(100, color=INK, lw=1.5)
    ax.text(101.5, 1.55, "100: one man for every woman", fontsize=8 * K, color=INK, va="center")
    ax.set_yticks(range(len(rows)), [r[0] for r in rows])
    ax.set_ylim(-0.6, 1.7)
    ax.invert_yaxis()
    ax.set_xlim(0, 210)
    tidy(ax)
    ax.set_title("Figure 4.1. Never-married men per 100 never-married women, ages 25 to 34, 1960 and 2012",
                 loc="left", fontsize=11 * K, color=INK, pad=10)
    note(fig, "Source: Pew Research Center, \"Record Share of Americans Have Never Married,\" 2014, from the 1960–2000 "
         "decennial census and the 2010–2012 American Community Survey (IPUMS).")
    save(fig, "fig-4-1-men-per-100-women")


# Figure 6.1 limits, one person, 2026 (sources.md items 42-44, 31)
EXTRA_HELP = 1995      # SSA EN-05-10508, after the $20 disregard
QI_LIMIT = 1816        # Medicare.gov, disregard folded in
CEAP_YEAR = 23940      # TDHCA, 150% of the guideline
TEFAP_YEAR = 29526     # Texas Department of Agriculture, 185% of the guideline


def fig_limits():
    """Figure 6.1: how far the average retiree's check sits from each program's limit."""
    b = ar.AVG_RETIRED
    rows = [  # dollars a month; positive = over the limit (she misses), negative = under (she qualifies)
        ("Extra Help (Medicare drug costs)", b - 20 - EXTRA_HELP),
        ("Medicare premium help (Qualifying Individual)", b - QI_LIMIT),
        ("Texas utility help (CEAP)", (b * 12 - CEAP_YEAR) / 12),
        ("Food bank (TEFAP)", (b * 12 - TEFAP_YEAR) / 12),
    ]
    fig, ax = plt.subplots(figsize=(8.5, 3.2))
    for i, (label, v) in enumerate(rows):
        ax.barh(i, v, height=0.55, color=SERIES[1] if v > 0 else SERIES[2])
        word = "over: she misses it" if v > 0 else "under: she qualifies"
        ax.text(max(v, 0) + 8, i, f"{money(abs(v))} {word}", va="center", ha="left", fontsize=9 * K, color=INK)
    ax.axvline(0, color=INK, lw=1.5)
    ax.set_yticks(range(len(rows)), [r[0] for r in rows])
    ax.invert_yaxis()
    ax.set_xlim(-620, 520)
    ax.xaxis.set_major_formatter(lambda x, _: ("−" if x < 0 else "+" if x > 0 else "") + money(abs(x)))
    ax.set_xlabel("Her check against the program's limit, dollars a month")
    tidy(ax)
    ax.set_title(f"Figure 6.1. The average retiree's {money(b)} check against each program's limit, 2026",
                 loc="left", fontsize=11 * K, color=INK, pad=10)
    note(fig, "One person, average retired-worker benefit (SSA, January 2026). Extra Help counts income after a \\$20 "
         "disregard. SNAP is not shown: she qualifies for the \\$25 minimum.\nSources: SSA EN-05-10508; Medicare.gov; "
         "Texas Department of Housing and Community Affairs; Texas Department of Agriculture. Details in sources.md.", y=-0.16)
    save(fig, "fig-6-1-program-limits")


def fig_side_income():
    """Figure 7.1: share of adults doing gig work in the past month, by age (Fed SHED 2024, Table 5)."""
    rows = [("18–29", 26), ("30–44", 24), ("45–59", 21), ("60 and older", 12)]
    fig, ax = plt.subplots(figsize=(8.5, 3.0))
    for i, (label, v) in enumerate(rows):
        ax.barh(i, v, height=0.55, color=SERIES[0])
        ax.text(v + 0.4, i, f"{v}%", va="center", fontsize=9 * K, color=INK)
    ax.axvline(20, color=INK, lw=1.2, ls="--")
    ax.text(20.3, -0.55, "All adults 20%", fontsize=8 * K, color=INK, va="bottom")
    ax.set_yticks(range(len(rows)), [r[0] for r in rows])
    ax.set_ylim(len(rows) - 0.5, -0.8)
    ax.set_xlim(0, 30)
    ax.xaxis.set_major_formatter(lambda x, _: f"{x:.0f}%")
    tidy(ax)
    ax.set_title("Figure 7.1. Adults who did gig work in the past month, by age, 2024",
                 loc="left", fontsize=11 * K, color=INK, pad=10)
    note(fig, "Gig activities as the Fed counts them: selling items, renting out property or a vehicle, and short-term tasks such as "
         "giving rides, delivering takeout or doing odd jobs.\n31% of those who did gig work say they would have trouble making ends meet without it.\nSource: Board of Governors of the Federal Reserve System, "
         "Economic Well-Being of U.S. Households in 2024, Tables 5 and 6.")
    save(fig, "fig-7-1-side-income-by-age")


def read_cpi_u(path):
    """Monthly CPI-U, not seasonally adjusted (BLS series CUUR0000SA0)."""
    out = {}
    with open(path) as f:
        for line in f:
            p = line.split("\t")
            if p[0].strip() == "CUUR0000SA0" and p[2].startswith("M") and p[2] != "M13" and p[3].strip() != "-":
                out[(int(p[1]), int(p[2][1:]))] = float(p[3])
    return out


def fig_1980s():
    """Figure 9.1: inflation and the prime rate, 1979-1982."""
    import csv
    base = os.path.dirname(os.path.abspath(__file__))
    cpi = read_cpi_u(os.path.join(base, "src/primary/04c-bls-cpi-u-cu.data.1.AllItems.txt"))
    with open(os.path.join(base, "src/gaps-a/c02-fred-mprime.csv")) as f:
        prime = {(int(r["observation_date"][:4]), int(r["observation_date"][5:7])): float(r["MPRIME"])
                 for r in csv.DictReader(f)}
    months = [(y, m) for y in range(1979, 1983) for m in range(1, 13)]
    x = [y + (m - 1) / 12 for y, m in months]
    infl = [100 * (cpi[(y, m)] / cpi[(y - 1, m)] - 1) for y, m in months]
    rate = [prime[k] for k in months]
    fig, ax = plt.subplots(figsize=(8.5, 3.8))
    ax.plot(x, rate, color=SERIES[0], lw=2)
    ax.plot(x, infl, color=SERIES[1], lw=2)
    ip, rp = infl.index(max(infl)), rate.index(max(rate))
    name = lambda k: f"{['January','February','March','April','May','June','July','August','September','October','November','December'][k[1]-1]} {k[0]}"
    ax.annotate(f"Inflation peaks at {max(infl):.1f}%\n({name(months[ip])})", (x[ip], infl[ip]), xytext=(1980.75, 3.5),
                fontsize=8 * K, color=INK, arrowprops=dict(arrowstyle="-", color=INK2, lw=0.8))
    ax.annotate(f"Prime rate, monthly average,\npeaks at {max(rate):.2f}% ({name(months[rp])})", (x[rp], rate[rp]),
                xytext=(x[rp] - 1.2, 21.3), fontsize=8 * K, color=INK, ha="right",
                arrowprops=dict(arrowstyle="-", color=INK2, lw=0.8))
    ax.text(x[-1] + 0.05, rate[-1], "Prime rate", fontsize=8 * K, color=SERIES[0], va="center")
    ax.text(x[-1] + 0.05, infl[-1], "Inflation\n(12-month change)", fontsize=8 * K, color=SERIES[1], va="center")
    ax.set_xlim(1979, 1983.6)
    ax.set_xticks([1979, 1980, 1981, 1982, 1983])
    ax.set_ylim(0, 24)
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:.0f}%")
    tidy(ax, "y")
    ax.set_title("Figure 9.1. Inflation and the prime rate, 1979–1982", loc="left", fontsize=11 * K, color=INK, pad=10)
    note(fig, "Inflation: 12-month change in the Consumer Price Index for All Urban Consumers, not seasonally adjusted. "
         "The daily prime rate reached 21.50% on 19 December 1980.\nSources: Bureau of Labor Statistics, series "
         "CUUR0000SA0; Board of Governors of the Federal Reserve System, bank prime loan rate (FRED MPRIME, DPRIME).")
    save(fig, "fig-9-1-inflation-and-prime-1979-1982")


LIFE_AT_62 = {"women": 23.08, "men": 20.29}  # SSA Period Life Table 2023 (sources.md item 49)


def runout_age(benefit, savings):
    bal = balances(benefit, savings)
    for a, (v0, v1) in enumerate(zip(bal, bal[1:]), start=62):
        if v0 >= 0 > v1:
            return a + v0 / (v0 - v1)
    return None


def fig_lifespan():
    """Figure 10.1: years a woman retiring at 62 can expect to live, against the year her savings run out."""
    labels = ["Average retiree", "Widow", "No retirement account"]
    end = 62 + LIFE_AT_62["women"]
    fig, ax = plt.subplots(figsize=(8.5, 3.0))
    for i, ((_, benefit, savings), name) in enumerate(zip(ar.CASES[1:], labels)):
        out = runout_age(benefit, savings) if savings else 62
        if out > 62:
            ax.barh(i, out - 62, left=62, height=0.55, color=SERIES[2])
        ax.barh(i, end - out, left=out, height=0.55, color=SERIES[1])
        ax.text(out + (end - out) / 2, i, f"{end - int(out):.0f} years with no savings", ha="center",
                va="center", fontsize=9 * K, color=INK)
        ax.text(61.8, i, f"runs out at {int(out)}" if out > 62 else "nothing saved", ha="right", va="center",
                fontsize=8 * K, color=INK2)
    ax.axvline(end, color=INK, lw=1.5)
    ax.text(end - 0.2, -0.55, f"Life expectancy at 62, women: {end:.1f}", ha="right", va="bottom", fontsize=8 * K, color=INK)
    ax.set_yticks(range(len(labels)), labels)
    ax.tick_params(axis="y", pad=62 * K)
    ax.set_ylim(len(labels) - 0.5, -0.8)
    ax.set_xlim(62, 87)
    ax.set_xticks(range(62, 88, 2))
    ax.set_xlabel("Age")
    tidy(ax)
    ax.set_title("Figure 10.1. A woman who retires at 62: savings against life expectancy",
                 loc="left", fontsize=11 * K, color=INK, pad=10)
    note(fig, "Green: years her savings cover the gap between her check and her costs. Orange: years left after they run out, "
         f"to average life expectancy for a woman at 62 ({LIFE_AT_62['women']} years).\nSources: SSA Period Life Table 2023, "
         "as used in the 2026 Trustees Report; savings run-out computed by arithmetic.py (Figure 5.1).", y=-0.16)
    save(fig, "fig-10-1-lifespan-against-run-out")


if __name__ == "__main__":
    fig_thesis()
    fig_line()
    fig_ledger()
    fig_runout()
    fig_price_to_income()
    fig_at_home()
    fig_men_per_women()
    fig_messages()
    fig_degree_dropped()
    fig_limits()
    fig_side_income()
    fig_1980s()
    fig_lifespan()
    print("wrote", sorted(os.listdir(OUT)))
