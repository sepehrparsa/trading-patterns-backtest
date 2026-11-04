"""Six ICT entry models with textbook rules. Each returns a list of trade results in R.
Definitions (all signals use closed candles only):
  FVG retrace     15m three-candle gap; limit at the gap edge, stop at the far side of candle 1.
  Order block     15m: a close beyond the 10-bar high/low; the last opposite candle before it is the block;
                  limit at its edge, stop at its far side.
  OTE             15m: a close beyond the 20-bar high/low; limit at the 70.5% retracement of the leg, stop beyond its start.
  Silver Bullet   5m: first fair value gap between 10:00 and 11:00 New York; limit at the gap edge; 2 hours max.
  Judas swing     5m: London (02:00-05:00 NY) sweeps the Asia range (20:00-00:00) and closes back inside;
                  market entry the other way, stop beyond the sweep; 6 hours max.
  Turtle soup     15m: the previous trading day's high/low is swept and the candle closes back inside;
                  market entry the other way, stop beyond the wick.
"""
import numpy as np
import pandas as pd
from common import Sim, arrays, bars


def run(m1, spread, pad, min_risk, rr=2.0):
    m5, m15 = bars(m1, "5min"), bars(m1, "15min")
    res = {}
    s15, s5 = Sim(m15, spread, min_risk), Sim(m5, spread, min_risk)
    O, H, L, C = arrays(m15)

    r = []
    for k in range(2, len(C) - 1):
        if L[k] > H[k - 2] and C[k - 1] > O[k - 1]:
            r.append(s15.trade(k, 1, H[k - 2], L[k - 2], rr, 48))
        if H[k] < L[k - 2] and C[k - 1] < O[k - 1]:
            r.append(s15.trade(k, -1, L[k - 2], H[k - 2], rr, 48))
    res["FVG retrace"] = r

    r = []
    for k in range(12, len(C) - 1):
        if C[k] > H[k - 10:k].max() and C[k] > O[k]:
            j = k - 1
            while j > k - 6 and C[j] >= O[j]:
                j -= 1
            if C[j] < O[j]:
                r.append(s15.trade(k, 1, H[j], L[j], rr, 48))
        if C[k] < L[k - 10:k].min() and C[k] < O[k]:
            j = k - 1
            while j > k - 6 and C[j] <= O[j]:
                j -= 1
            if C[j] > O[j]:
                r.append(s15.trade(k, -1, L[j], H[j], rr, 48))
    res["Order block"] = r

    r = []
    for k in range(21, len(C) - 1):
        if C[k] > H[k - 20:k].max():
            lo, hi = L[k - 20:k + 1].min(), H[k]
            r.append(s15.trade(k, 1, hi - 0.705 * (hi - lo), lo - pad, rr, 48, wait=30))
        if C[k] < L[k - 20:k].min():
            hi, lo = H[k - 20:k + 1].max(), L[k]
            r.append(s15.trade(k, -1, lo + 0.705 * (hi - lo), hi + pad, rr, 48, wait=30))
    res["OTE 70.5%"] = r

    O5, H5, L5, C5 = arrays(m5)
    T5 = m5.index
    hour, day = T5.hour.values, T5.normalize().values
    r, last = [], None
    for k in range(2, len(C5) - 1):
        if hour[k] != 10 or last == day[k]:
            continue
        if L5[k] > H5[k - 2]:
            r.append(s5.trade(k, 1, H5[k - 2], L5[k - 2], rr, 24, wait=12)); last = day[k]
        elif H5[k] < L5[k - 2]:
            r.append(s5.trade(k, -1, L5[k - 2], H5[k - 2], rr, 24, wait=12)); last = day[k]
    res["Silver Bullet"] = r

    r = []
    for d0 in T5.normalize().unique():
        a, b = T5.searchsorted(d0 - pd.Timedelta(hours=4)), T5.searchsorted(d0)
        s0, s1 = T5.searchsorted(d0 + pd.Timedelta(hours=2)), T5.searchsorted(d0 + pd.Timedelta(hours=5))
        if b - a < 30 or s1 - s0 < 20:
            continue
        ah, al = H5[a:b].max(), L5[a:b].min()
        for k in range(s0, s1):
            if H5[k] > ah and C5[k] < ah:
                r.append(s5.trade(k, -1, C5[k], H5[k] + pad, rr, 72, limit=False)); break
            if L5[k] < al and C5[k] > al:
                r.append(s5.trade(k, 1, C5[k], L5[k] - pad, rr, 72, limit=False)); break
    res["Judas swing"] = r

    r = []
    td = ((m15.index - pd.Timedelta(hours=18)).normalize()).values     # trading day starts 18:00 NY
    days = np.unique(td)
    pos = {d: i for i, d in enumerate(days)}
    dh = {d: H[td == d].max() for d in days}
    dl = {d: L[td == d].min() for d in days}
    used = set()
    for k in range(1, len(C) - 1):
        i = pos[td[k]]
        if i == 0:
            continue
        p = days[i - 1]
        if (td[k], "h") not in used and H[k] > dh[p] and C[k] < dh[p]:
            used.add((td[k], "h")); r.append(s15.trade(k, -1, C[k], H[k] + pad, rr, 48, limit=False))
        if (td[k], "l") not in used and L[k] < dl[p] and C[k] > dl[p]:
            used.add((td[k], "l")); r.append(s15.trade(k, 1, C[k], L[k] - pad, rr, 48, limit=False))
    res["Turtle soup"] = r
    return res


def random_baseline(m1, spread, min_risk, rr=2.0, n=6000, seed=3):
    """Random 15m market entries, random side, stop 1 x ATR(14), same target and max hold."""
    from common import atr
    m15 = bars(m1, "15min")
    s, a = Sim(m15, spread, min_risk), atr(m15)
    C = m15.c.values
    rng = np.random.default_rng(seed)
    out = []
    for k in rng.choice(np.arange(20, len(C) - 60), n, replace=False):
        d = rng.choice([-1, 1])
        e = C[k]
        stop = (e + (spread if d > 0 else 0)) - d * a[k]
        out.append(s.trade(k, d, e, stop, rr, 48, limit=False))
    return out
