# Do popular trading patterns, ICT and Smart Money setups have an edge?

Code and results behind the article *Why Most Trading Strategies You See on Social Media Lose Money*.

**Short answer: in 87,563 test trades, none of the tested patterns or models made money after costs.**

Everything here is plain Python. Every rule is written out in code so anyone can check it, argue with it, or change it.

## What is tested

| Script | What it does | Trades |
| --- | --- | --- |
| `run_patterns.py` | 11 price-action and Smart Money patterns on gold (15-minute), 1R target | 14,204 |
| `run_ict.py` | 6 ICT entry models; gold at 1R / 2R / 3R, EURUSD / GBPUSD / Dow Jones at 2R | 73,359 |
| `run_simulations.py` | The three simulations in the article (survivorship, spread vs stop, drawdown risk) | no market data |

Each test also runs **random entries** with the same exits, so every result has a baseline.

## Rules used

All signals use closed candles only. Times are New York time. Costs: gold $0.34 spread, EURUSD and GBPUSD 0.7 pips, Dow Jones 2 points. A bar that touches both stop and target counts as a loss. Buys pay the spread on entry, sells on exit; a limit buy fills only when the ask reaches it.

**Patterns (`run_patterns.py`)**: entry at the close of the signal candle, stop and target 1 x ATR(14), 4 hours max.
- Swings: a high (low) above (below) the 3 candles on each side, used only after those 3 candles have closed.
- Break of structure: a close through the last confirmed swing in the same direction as the previous break; market structure shift: in the opposite direction.
- Double top / bottom: two swings within 0.22 ATR, 7+ candles apart, confirmed by a close through the neckline. Triple touch: three such swings.
- Equal highs / lows: two such swings; the first later candle that trades through them is a *sweep reversal* if it closes back, else a *break*.
- Session ranges (Asia 18:00-02:00, London 02:00-07:00, New York 07:00-12:00): first close beyond the range after the session = breakout; a close back inside = false break (faded); a touch that holds = retest.

**ICT models (`src/ict_models.py`)**: see the docstring. Fair value gap retrace, order block, OTE 70.5%, Silver Bullet (10:00-11:00 NY), Judas swing (London sweep of the Asia range), turtle soup (previous-day high/low sweep).

These are textbook definitions. Others define the models differently; the code is short so you can test your own version.

## Results

### Patterns on gold, 1R (win rate in %, profit factor after spread)

| pattern | trades | win_rate | avg_r | profit_factor |
|---|---|---|---|---|
| Triple touch | 47 | 55.3 | -0.011 | 0.98 |
| False break (fade) | 2462 | 51.0 | -0.06 | 0.88 |
| Double top / bottom | 568 | 49.6 | -0.099 | 0.82 |
| Retest of a session level | 1742 | 49.4 | -0.081 | 0.85 |
| Random entries | 33506 | 49.3 | -0.101 | 0.81 |
| Break of structure (BOS) | 3454 | 48.8 | -0.118 | 0.79 |
| Asia range breakout | 938 | 48.7 | -0.116 | 0.79 |
| Equal highs / lows break | 358 | 48.3 | -0.133 | 0.77 |
| Liquidity sweep reversal | 345 | 48.1 | -0.136 | 0.76 |
| Market structure shift (MSS) | 2354 | 48.0 | -0.134 | 0.76 |
| London range breakout | 1048 | 46.1 | -0.152 | 0.74 |
| New York range breakout | 888 | 44.6 | -0.18 | 0.69 |

### ICT models on gold, 2R

| model | trades | win_rate | profit_factor |
|---|---|---|---|
| FVG retrace | 6242 | 29.9 | 0.83 |
| Order block | 3857 | 27.7 | 0.75 |
| OTE 70.5% | 198 | 26.8 | 0.72 |
| Silver Bullet | 317 | 27.8 | 0.67 |
| Judas swing | 456 | 22.8 | 0.59 |
| Turtle soup | 616 | 32.3 | 0.89 |
| Random entries | 6000 | 30.0 | 0.85 |

### ICT models, profit factor after spread, every target and market

| model | EURUSD 2R | GBPUSD 2R | US30 2R | XAUUSD 1R | XAUUSD 2R | XAUUSD 3R |
|---|---|---|---|---|---|---|
| FVG retrace | 0.75 | 0.76 | 0.81 | 0.72 | 0.83 | 0.84 |
| Order block | 0.71 | 0.72 | 0.85 | 0.66 | 0.75 | 0.82 |
| OTE 70.5% | 0.7 | 0.75 | 0.83 | 0.49 | 0.72 | 0.92 |
| Silver Bullet | 0.71 | 0.71 | 0.93 | 0.61 | 0.67 | 0.77 |
| Judas swing | 0.9 | 0.79 | 0.73 | 0.51 | 0.59 | 0.71 |
| Turtle soup | 0.93 | 0.78 | 0.89 | 0.7 | 0.89 | 0.9 |
| Random entries | 0.73 | 0.79 | 0.87 | 0.75 | 0.85 | 0.88 |

A profit factor below 1.0 loses money. Not one of the 36 ICT combinations reached 1.0.

## Data

Not included (licence). Put the files in `data/`:

- Gold: [Dukascopy historical data export](https://www.dukascopy.com/swiss/english/marketwatch/historical/), XAUUSD, 1 minute, bid, 2024-01-01 to 2026-10-31, CSV with a `timestamp` column in milliseconds (UTC). Save as `data/xauusd-m1-bid-2024-01-01-2026-10-31.csv`.
- EURUSD, GBPUSD, Dow Jones: any 1-minute source. The published results used a broker's MetaTrader 5 export (tab separated, times in UTC), saved as `data/EURUSD_M1.csv`, `data/GBPUSD_M1.csv`, `data/US30_M1.csv`. Dukascopy CSVs work too.

## Run

```
pip install -r requirements.txt
python run_patterns.py
python run_ict.py
python run_simulations.py
```

Results are written to `results/`. A full run takes about a minute. `run_ict.py` skips any market whose data file is missing and writes only the markets it ran.

## Limits

- One definition per model, one period (Jan 2024 to Oct 2026), fixed exits. A different definition could give a different result; that is why the code is public.
- Backtests do not see slippage, partial fills or execution mistakes, so live results would be lower, not higher.
- Past results do not guarantee future results. This is research and education, not financial advice.

## Licence

MIT
