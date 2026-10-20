#!/usr/bin/env python3
"""Share of adults who sold items for money in the past month, by age, weighted.

Data: Federal Reserve, Survey of Household Economics and Decisionmaking (SHED) 2024,
public file src/gaps-b/b10-shed-2024-csv/public2024.csv; codebook src/gaps-b/b09.
GE2A: "In the past month, have you made money by selling items in any of these ways?"
(flea markets, garage sales, eBay, Etsy), coded "Yes"/"No" in the CSV. ppage: age in years. weight: the
survey's sample weight. Run: python3 shed.py
"""
import csv
import os

PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    "src/gaps-b/b10-shed-2024-csv/public2024.csv")
BANDS = [("18-29", 18, 29), ("30-44", 30, 44), ("45-59", 45, 59), ("60+", 60, 200)]


def main():
    sold, total = {}, {}
    with open(PATH, newline="") as f:
        for row in csv.DictReader(f):
            age, w = int(row["ppage"]), float(row["weight"])
            for name, lo, hi in BANDS + [("all", 18, 200)]:
                if lo <= age <= hi:
                    total[name] = total.get(name, 0) + w
                    sold[name] = sold.get(name, 0) + w * (row["GE2A"] == "Yes")
    for name, *_ in BANDS + [("all",)]:
        print(f"{name:6} sold items in the past month: {100 * sold[name] / total[name]:5.1f}%")


if __name__ == "__main__":
    main()
