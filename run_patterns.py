"""Price-action / SMC pattern test on gold (15-minute bars).
Entry at the close of the signal candle, stop and target 1 x ATR(14), 4 hours max, $0.34 spread.
Writes results/pattern_results.csv. Random entries are the comparison."""
import sys, os, bisect
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
import numpy as np, pandas as pd
from common import load_m1, bars, atr

PATH, COST = "data/xauusd-m1-bid-2024-01-01-2026-10-31.csv", 0.34
m1 = load_m1(PATH)
m = bars(m1, "15min")
O, H, L, C = m.o.values, m.h.values, m.l.values, m.c.values
n, T = len(C), m.index
ATR = atr(m)
h1 = m1.c.resample("1h").last().dropna()
h1t, h1c = h1.index.values, h1.values


def h1_bias(k):
    """Direction of the last 4 closed H1 candles before the close of bar k."""
    t = T.values[k] + np.timedelta64(15, "m")
    j = np.searchsorted(h1t, t - np.timedelta64(1, "h"), side="right") - 1
    if j < 4:
        return 0
    return 1 if h1c[j] > h1c[j - 4] else -1 if h1c[j] < h1c[j - 4] else 0


def outcome(k, d, hold=16):
    if k + 1 >= n or not ATR[k] > 0:
        return None
    R, en = ATR[k], C[k]
    tp, sl = en + d * R, en - d * R
    for y in range(k + 1, min(n, k + 1 + hold)):
        if (d > 0 and L[y] <= sl) or (d < 0 and H[y] >= sl):
            return -1 - COST / R
        if (d > 0 and H[y] >= tp) or (d < 0 and L[y] <= tp):
            return 1 - COST / R
    y = min(n - 1, k + hold)
    return (C[y] - en) * d / R - COST / R


ev, w = [], 3
ph = [i for i in range(w, n - w) if all(H[i] > H[i - j] and H[i] > H[i + j] for j in range(1, w + 1))]
pl = [i for i in range(w, n - w) if all(L[i] < L[i - j] and L[i] < L[i + j] for j in range(1, w + 1))]
# structure: a close through the last CONFIRMED swing (w candles after it)
last = 0
for k in range(50, n):
    a, b = bisect.bisect_right(ph, k - w - 1) - 1, bisect.bisect_right(pl, k - w - 1) - 1
    if a < 0 or b < 0:
        continue
    tol = ATR[k] * 0.22
    hl, ll = H[ph[a]], L[pl[b]]
    up = C[k] > hl + tol * .15 and C[k - 1] <= hl + tol * .15
    dn = C[k] < ll - tol * .15 and C[k - 1] >= ll - tol * .15
    if up == dn:
        continue
    d = 1 if up else -1
    shift = last != 0 and d != last
    last = d
    if shift:
        ev.append(("Market structure shift (MSS)", k, d))
    else:
        ev.append(("Break of structure (BOS)", k, d))
# double / triple, equal highs / lows
for side, P in ((1, ph), (-1, pl)):
    X = H if side == 1 else L
    for z in range(1, len(P)):
        a, c = P[z - 1], P[z]
        if c - a < 7:
            continue
        tol = ATR[c] * 0.22
        if abs(X[a] - X[c]) > tol:
            continue
        neck = L[a:c + 1].min() if side == 1 else H[a:c + 1].max()
        for q in range(c + w, min(n, c + 60)):
            if (side == 1 and C[q] < neck) or (side == -1 and C[q] > neck):
                ev.append(("Double top / bottom", q, -side)); break
        for q in range(c + w, min(n, c + 200)):
            if (side == 1 and H[q] > max(X[a], X[c])) or (side == -1 and L[q] < min(X[a], X[c])):
                lvl = max(X[a], X[c]) if side == 1 else min(X[a], X[c])
                back = (C[q] < lvl) if side == 1 else (C[q] > lvl)
                ev.append(("Liquidity sweep reversal" if back else "Equal highs / lows break", q, -side if back else side)); break
        if z >= 2:
            d0 = P[z - 2]
            if a - d0 >= 7 and abs(X[d0] - X[a]) <= tol and abs(X[d0] - X[c]) <= tol:
                ev.append(("Triple touch", c + w, -side))
# sessions (New York time): Asia 18-02, London 02-07, New York 07-12
nyh = T.hour.values + T.minute.values / 60
nyd = (T - pd.Timedelta(hours=18)).normalize().values
for name, (a0, a1) in {"Asia": (18, 2), "London": (2, 7), "New York": (7, 12)}.items():
    ins = ((nyh >= a0) | (nyh < a1)) if a0 > a1 else ((nyh >= a0) & (nyh < a1))
    for _, idx in pd.Series(np.arange(n))[ins].groupby(nyd[ins]):
        idx = idx.values
        if len(idx) < 8:
            continue
        sh, sl_, e = H[idx].max(), L[idx].min(), idx[-1] + 1
        for d, lvl in ((1, sh), (-1, sl_)):
            br = None
            for k in range(e, min(n, e + 120)):
                tol = ATR[k] * 0.22
                if (d > 0 and C[k] > lvl + tol * .25 and C[k - 1] <= lvl + tol * .25) or (d < 0 and C[k] < lvl - tol * .25 and C[k - 1] >= lvl - tol * .25):
                    br = k; break
            if br is None:
                continue
            ev.append((f"{name} range breakout", br, d))
            ret = None
            for k in range(br + 1, min(n, br + 120)):
                tol = ATR[k] * 0.22
                if (d > 0 and C[k] < lvl - tol * .25) or (d < 0 and C[k] > lvl + tol * .25):
                    ev.append(("False break (fade)", k, -d)); break
                if ret is None and ((d > 0 and L[k] <= lvl + tol and C[k] > lvl) or (d < 0 and H[k] >= lvl - tol and C[k] < lvl)):
                    ret = k; ev.append(("Retest of a session level", k, d))
E = pd.DataFrame(ev, columns=["pattern", "k", "d"])
E["r"] = [outcome(k, d) for k, d in zip(E.k, E.d)]
E = E.dropna()
rng = np.random.default_rng(7)
base = [outcome(k, d) for k in np.arange(50, n - 20, 4) for d in (1, -1)]


def st(r):
    r = np.array(r)
    return dict(trades=len(r), win_rate=round(100 * (r > 0).mean(), 1), avg_r=round(r.mean(), 3), profit_factor=round(r[r > 0].sum() / -r[r < 0].sum(), 2))


rows = [dict(pattern=p, **st(g.r)) for p, g in E.groupby("pattern")] + [dict(pattern="Random entries", **st(base))]
out = pd.DataFrame(rows).sort_values("win_rate", ascending=False)
os.makedirs("results", exist_ok=True)
out.to_csv("results/pattern_results.csv", index=False)
print(out.to_string(index=False))
