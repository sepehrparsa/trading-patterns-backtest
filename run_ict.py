"""Runs the six ICT models on every market and target and writes results/ict_results.csv."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
import pandas as pd
from common import load_m1, stats
import ict_models

# path, spread, stop pad, minimum risk (price units)
MARKETS = {
    "XAUUSD": ("data/xauusd-m1-bid-2024-01-01-2026-10-31.csv", 0.34, 0.10, 0.50),
    "EURUSD": ("data/EURUSD_M1.csv", 0.00007, 0.00002, 0.00010),
    "GBPUSD": ("data/GBPUSD_M1.csv", 0.00007, 0.00002, 0.00010),
    "US30":   ("data/US30_M1.csv", 2.0, 1.0, 5.0),
}
TARGETS = {"XAUUSD": [1.0, 2.0, 3.0], "EURUSD": [2.0], "GBPUSD": [2.0], "US30": [2.0]}

rows = []
for mk, (path, sp, pad, mr) in MARKETS.items():
    if not os.path.exists(path):
        print("skip", mk, "(no data file)"); continue
    m1 = load_m1(path)
    for rr in TARGETS[mk]:
        for model, r in ict_models.run(m1, sp, pad, mr, rr).items():
            rows.append(dict(market=mk, target_r=rr, model=model, **stats(r)))
        rows.append(dict(market=mk, target_r=rr, model="Random entries", **stats(ict_models.random_baseline(m1, sp, mr, rr))))
        print(mk, rr, "done")
os.makedirs("results", exist_ok=True)
pd.DataFrame(rows).to_csv("results/ict_results.csv", index=False)
print(pd.DataFrame(rows).to_string())
