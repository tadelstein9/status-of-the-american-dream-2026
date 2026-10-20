# Status of the American Dream 2026

*Changes in Sociological Trends Subvert the Constitutional Republic*

By Tom Adelstein. Read the study on [Substack](https://tomadelstein.substack.com/p/status-of-the-american-dream-2026).

This repository holds the scripts behind the study's numbers and figures, so a reader can run each worked case and check it against the public record. Every input in a script names the document and page it came from, and the endnotes in `report/report.md` give each document in full.

## What each script computes

| Script | What it computes | Saved output |
|---|---|---|
| `youth.py` | The 25-year-old father: take-home pay after 2026 federal taxes and credits, and the monthly cost of starting a household, nationally and in Texas | `youth-output.txt` |
| `arithmetic.py` | Four retirees who start at 62 in January 2026: the year each one's savings run out, with prices and benefits rising at their measured rates | `arithmetic-output.txt` |
| `shed.py` | The weighted share of adults, by age, who earned money selling items in the past month (Federal Reserve SHED 2024, question GE2A) | `shed-output.txt` |
| `figures.py` | Figures 1.1 through 10.1 as PNG and SVG files in `figures/` | |

`youth.py` and `arithmetic.py` carry their inputs inside the script, each with its source in a comment. `shed.py` and `figures.py` read the public data files in `src/`.

## Running them

The scripts need Python 3. `figures.py` also needs matplotlib, openpyxl and xlrd.

```
python3 youth.py
python3 arithmetic.py
cd src/gaps-b/b10-shed-2024-csv && unzip shed2024-csv.zip && cd -
python3 shed.py
pip install matplotlib openpyxl xlrd
python3 figures.py
```

Each run should match its saved output file.

## Data files

The repository includes these public files:

- `src/gaps-b/b10-shed-2024-csv/shed2024-csv.zip`: Federal Reserve, Survey of Household Economics and Decisionmaking 2024 public data ([download page](https://www.federalreserve.gov/consumerscommunities/shed_data.htm)).
- `src/primary/04c-bls-cpi-u-cu.data.1.AllItems.txt`: Bureau of Labor Statistics, CPI-U ([cu.data.1.AllItems](https://download.bls.gov/pub/time.series/cu/cu.data.1.AllItems)).
- `src/gaps-a/c02-fred-mprime.csv`: Federal Reserve Bank of St. Louis, FRED series [MPRIME](https://fred.stlouisfed.org/series/MPRIME), the monthly bank prime loan rate.
- `src/youth/raw/y09b-census-ad1-table.xls`: Census Bureau, table AD-1, young adults living at home ([table page](https://www.census.gov/data/tables/time-series/demo/families/adults.html)).

Figure 3.1 reads Table W-16 of the appendix tables to the Harvard Joint Center for Housing Studies' *State of the Nation's Housing 2026*. Harvard publishes that workbook, so this repository leaves it out. Download it from the [report page](https://www.jchs.harvard.edu/state-nations-housing-2026) and save it as `src/primary/07e-jchs-son-2026-appendix.xlsx`; until then, `figures.py` skips Figure 3.1 and draws the rest.

The other documents the study cites, such as reports, fact sheets, rule books and filings, appear in the endnotes with their publisher, date and page.

## What the scripts leave out

Savings earn no return in the retiree cases, and the scripts charge no income tax on the retiree's benefit or withdrawals. A return would push each run-out age later; a tax would pull it earlier. The program limits come from federal rules and from Texas, and other states set some of them differently. `report/report.md` describes the method in full under "Methods".

## License

The code carries the MIT License (`LICENSE`). The text of the study and its figures belong to Tom Adelstein, all rights reserved.
