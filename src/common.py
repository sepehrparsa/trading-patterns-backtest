"""Shared helpers: data loading, bar building and the trade simulator used by every test."""
import numpy as np
import pandas as pd

NY = "America/New_York"


def load_m1(path):
    """Load 1-minute bars. Supports a Dukascopy CSV export (timestamp in ms, UTC)
    and a MetaTrader 5 export (tab separated, <DATE> <TIME> ..., times in UTC).
    Returns a DataFrame with columns o h l c, indexed by New York time (time-zone aware,
    so resampling across the daylight-saving changes stays correct)."""
    head = open(path, encoding="utf-8", errors="ignore").readline()
    if head.startswith("timestamp"):
        d = pd.read_csv(path)
        t = pd.to_datetime(d.timestamp, unit="ms", utc=True)
        o, h, l, c = d.open, d.high, d.low, d.close
    else:
        d = pd.read_csv(path, sep="\t")
        d.columns = [x.strip("<>") for x in d.columns]
        t = pd.to_datetime(d.DATE + " " + d.TIME, format="%Y.%m.%d %H:%M:%S").dt.tz_localize("UTC")
        o, h, l, c = d.OPEN, d.HIGH, d.LOW, d.CLOSE
    idx = pd.DatetimeIndex(t.dt.tz_convert(NY))
    return pd.DataFrame({"o": o.values, "h": h.values, "l": l.values, "c": c.values}, index=idx)


def bars(m1, rule):
    """Resample 1-minute bars to a larger timeframe ("5min", "15min")."""
    return m1.resample(rule).agg({"o": "first", "h": "max", "l": "min", "c": "last"}).dropna()


def arrays(b):
    return b.o.values, b.h.values, b.l.values, b.c.values


def atr(b, n=14):
    o, h, l, c = arrays(b)
    tr = np.maximum(h[1:] - l[1:], np.maximum(abs(h[1:] - c[:-1]), abs(l[1:] - c[:-1])))
    return pd.Series(np.r_[h[0] - l[0], tr]).rolling(n).mean().values


class Sim:
    """Simulates one trade on bid prices. Buys pay the spread on entry, sells pay it on exit.
    A limit buy fills only when the bid trades `spread` below the limit (the ask touches it).
    A bar that touches both stop and target counts as a loss (conservative).
    Result is in R (risk units), costs included."""

    def __init__(self, b, spread, min_risk):
        self.O, self.H, self.L, self.C = arrays(b)
        self.n = len(self.C)
        self.sp = spread
        self.min_risk = min_risk

    def trade(self, k, d, entry, stop, rr, max_bars, limit=True, wait=20):
        O, H, L, C, sp = self.O, self.H, self.L, self.C, self.sp
        if not limit and d > 0:
            entry = entry + sp                       # market buy at the ask
        risk = abs(entry - stop)
        if risk < self.min_risk or (stop - entry) * d >= 0:
            return None
        tp = entry + d * rr * risk
        s = k + 1
        if limit:
            fill = None
            for y in range(k + 1, min(self.n, k + 1 + wait)):
                if (d > 0 and L[y] <= entry - sp) or (d < 0 and H[y] >= entry):
                    fill = y
                    break
                if (d > 0 and H[y] >= tp) or (d < 0 and L[y] + sp <= tp):
                    return None                      # ran to the target without a fill
            if fill is None:
                return None
            s = fill
        for y in range(s, min(self.n, s + max_bars)):
            if (d > 0 and L[y] <= stop) or (d < 0 and H[y] + sp >= stop):
                return -1.0
            if y > s and ((d > 0 and H[y] >= tp) or (d < 0 and L[y] + sp <= tp)):
                return float(rr)
        y = min(self.n - 1, s + max_bars)
        return ((C[y] - entry) * d - (sp if d < 0 else 0)) / risk


def stats(r):
    r = np.array([x for x in r if x is not None], dtype=float)
    if len(r) == 0:
        return dict(trades=0, win_rate=np.nan, avg_r=np.nan, profit_factor=np.nan)
    pf = r[r > 0].sum() / max(1e-12, -r[r < 0].sum())
    return dict(trades=len(r), win_rate=round(100 * (r > 0).mean(), 1), avg_r=round(r.mean(), 3), profit_factor=round(pf, 2))
