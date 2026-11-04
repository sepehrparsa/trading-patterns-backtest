"""The three simulations in the article. No market data needed. Writes results/simulations.txt."""
import numpy as np

out = []
rng = np.random.default_rng(7)
# 1) survivorship: 1,000 traders, 100 coin-flip trades at 1:1, 0.1R cost per trade
w = rng.random((1000, 100)) < 0.5
tot = (np.where(w, 1, -1) - 0.1).sum(1)
h, _ = np.histogram(tot, bins=np.arange(-50, 41, 10))
out.append(f"Survivorship: mean {tot.mean():.1f}R, at or above 0R: {(tot >= 0).sum()}, 10R or more: {(tot >= 10).sum()}, "
           f"win rate 60%+: {(w.mean(1) >= 0.6).sum()} of 1000")
out.append("  histogram -50..40 step 10: " + str(h.tolist()))
# 2) spread vs stop: 52% win at 1:1 = +0.04R before costs, $0.34 spread
out.append("Spread: " + ", ".join(f"${s}: {0.04 - 0.34 / s:+.3f}R" for s in [2, 3, 4, 5, 6, 8, 10, 15, 20]) + f"; break-even stop ${0.34 / 0.04:.1f}")
# 3) chance of a 10% drawdown within 200 trades, 50% win at 1:1, 0.05R cost
for rp in [0.5, 1, 2, 3, 5]:
    x = np.where(rng.random((20000, 200)) < 0.5, 1, -1) - 0.05
    eq = np.cumprod(1 + x * rp / 100, axis=1)
    out.append(f"Drawdown: risk {rp}% per trade -> {100 * (eq.min(1) <= 0.9).mean():.1f}% of accounts reach -10%")
# 4) longest losing streak in 200 coin flips
r = np.random.default_rng(1).random((20000, 200)) < 0.5
def longest(a):
    m = c = 0
    for v in a:
        c = c + 1 if v else 0
        m = max(m, c)
    return m
L = np.array([longest(v) for v in r])
out.append(f"Streaks: a run of 7+ losses in 200 trades happens in {100 * (L >= 7).mean():.0f}% of cases")
open("results/simulations.txt", "w").write("\n".join(out) + "\n")
print("\n".join(out))
