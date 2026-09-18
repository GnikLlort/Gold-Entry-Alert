# Gold-Entry-Alert — XAUUSD Smart Entry Engine (Pine Script v6, INDICATOR ONLY)

`XAUUSD_Smart_Entry_Engine.pine` is a complete **TradingView indicator** (built with `indicator()`)
that maps XAUUSD liquidity in real time and highlights **high-confluence** long / short setups using
a strict market-structure sequence.

It contains **no `strategy()` calls, no simulated orders and no order submission of any kind.**
Every entry, stop and target it prints is **analytical / hypothetical only**.

---

## 1. What it does

The engine continuously answers one question:

> *What is Gold doing right now, where is the liquidity, what has already happened, and what still
> needs to happen before a high-confluence entry becomes valid?*

It builds that answer from a fixed chain of events — it does **not** fire signals from RSI / MACD /
moving-average crosses:

```
HTF structure (H4 + H1)  →  environment / bias
        ↓
Liquidity map (PDH/PDL, PWH/PWL, Asia/London/NY, swings, equal highs & lows)
        ↓
Liquidity sweep (wick through the level + close back through it)
        ↓
Displacement (ATR + body + close-location)
        ↓
MSS / CHoCH (internal structure break on the structure timeframe)
        ↓
Fair Value Gap  →  entry zone
        ↓
Retracement + confirmation  →  suggested entry
        ↓
Logical liquidity targets  →  TP1 / TP2 / TP3
        ↓
Risk / reward + confluence  →  setup quality score
```

Each step is displayed on the chart and in the dashboard, so the chart always shows **why** the
engine is waiting, arming, or invalidating.

### Setup state machine

```
WAITING → LIQUIDITY APPROACHING → LIQUIDITY SWEPT → DISPLACEMENT → MSS CONFIRMED
        → SETUP ARMED → ENTRY ZONE → ENTRY CONFIRMED → TP1 HIT → TP2 HIT → TP3 HIT
                                                    ↘ INVALIDATED (with a reason)
```

Highly visible market states: `WAIT · WATCH · SWEEP · CONFIRMING · ARMED · ENTRY ZONE · LONG ·
SHORT · INVALIDATED`.

---

## 2. Installation

1. Download the **raw** file (GitHub → *Raw*, or `git clone`), not a rendered preview.
2. Open TradingView → **Pine Editor** → new **Indicator**, paste the whole file, **Save**, **Add to chart**.
3. Recommended chart: **XAUUSD, 5-minute** (execution timeframe). The indicator reads
   H4 / H1 / M15 internally, no matter what chart you are on.
4. Create alerts with *Alert → Condition → "XAUUSD Smart Entry Engine" → "Any alert() function call"*
   (one alert is enough — every message is dynamic and self-describing).

### Whitespace, pasting and line numbers

Pine blocks are **indentation based**, and TradingView's editor strips blank lines, so:

* **Never let the leading spaces be eaten.** This file uses **4 spaces per level, no tabs**.
  If a paste path collapses runs of spaces, every `if` / `for` body ends up at column 0 and
  nothing compiles. Fixes, in order:
  1. paste from the **raw** file (not from a rendered HTML preview or a chat message), or
  2. use **`XAUUSD_Smart_Entry_Engine.tabs.pine`** — a byte-identical copy that uses
     **one tab per level**; tabs survive paste paths that eat spaces, or
  3. if all indentation is gone, ask for a re-indented copy.
* **Every statement is on one line — nothing is ever wrapped.** Pine's continuation rule is
  indentation based (a wrapped line must be indented *more* than the statement it belongs to),
  and that is what produces `Syntax error at input "end of line without line continuation"`.
  With no wrapped lines at all, the only indentation the compiler reads is block indentation:
  one level of 4 spaces per `if` / `for` / `else` / function body. Every statement-start indent
  is a multiple of 4, so an editor re-indent keeps the block structure intact.
* **Line numbers will not match.** TradingView removes the file's blank lines, so an error at
  TradingView line `N` sits around file line `N + (blank lines before it)`. Easier: search for the
  **section header** (`// 11 -` = state machine, `// 7 -` = liquidity + sweeps, …), or paste the
  error text — the token and column identify the spot, not the number.

---

## 3. Default configuration (tuned for XAUUSD)

| Group | Default | Notes |
|---|---|---|
| HTF 1 / HTF 2 | `240` / `60` | macro bias / directional bias |
| Structure TF | `15` | internal swings used for MSS / CHoCH |
| Execution TF | `5` | informational — run the chart on it |
| Major / internal / micro swing length | `5` / `3` / `3` | pivots |
| Displacement | `1.2 × ATR`, body ≥ `50 %`, close in top/bottom `60 %` | gold impulse filter |
| Sweep penetration | `max(0.20 price, 0.10 × ATR)` | stops every random wick being called a sweep |
| Sweep validity | `2` bars to close back through | otherwise the level is `BROKEN`, not `SWEPT` |
| FVG | min `max(0.10 price, 0.15 × ATR)`, entry depth `50 %` | three-candle imbalance |
| Stop loss | sweep wick ± `0.25 × ATR`, min `0.30 × ATR`, max `2.50 × ATR` | `NO TRADE – SL TOO WIDE` otherwise |
| Targets | `Liquidity + Structure`, min R:R `1.50` | `NO TRADE – INSUFFICIENT TARGET SPACE` otherwise |
| Entry mode | `Balanced` (touch + rejection candle) | `Aggressive` / `Confirmation` also available |
| Sensitivity | `Balanced` | HTF may not oppose the trade |
| Max active setups | `1` | up to 3 |

Sessions default to **UTC** (`Asia 0000-0700`, `London 0700-1200`, `New York 1200-2000`) and are
evaluated in a configurable IANA timezone, so daylight-saving changes are handled by TradingView and
no fixed local clock is assumed.

---

## 4. Chart elements

| Element | Meaning |
|---|---|
| Dashed amber rays + labels | liquidity levels (PDH/PDL, PWH/PWL, Asia/London/NY H-L, swings, EQH/EQL) with state: `UNTOUCHED · APPROACHING · TESTED · POTENTIAL SWEEP · LIQUIDITY TAKEN · BROKEN` |
| Purple vertical raid + `SSL SWEPT` / `BSL SWEPT` | liquidity raid (level → extreme wick → close back) |
| `DISPLACEMENT` label | ATR-confirmed impulse candle |
| `MSS ↑` / `MSS ↓` | market structure shift on the structure timeframe |
| Blue boxes | fair value gaps (extended until filled, then greyed) |
| Brown boxes | order blocks created by displacement |
| Green / red background boxes | premium / discount dealing range + 50 % equilibrium |
| Dotted session boxes | completed Asia / London / New York ranges |
| FVG entry-zone box + `ENTRY / SL / TP1 / TP2 / TP3` lines | the analytical trade map |
| `LONG` / `SHORT` label | entry confirmed |
| Big label on the last bar | current market state |

Every component can be switched off individually (Visuals group).

---

## 5. Dashboard

A compact panel (top-right by default) with:

* HTF 1 / HTF 2 bias, alignment (`BULLISH / BEARISH / NEUTRAL / MIXED`), structure-TF bias
* Session and volatility regime (`LOW / NORMAL / HIGH / EXTREME`)
* Nearest liquidity pool, distance in price and ATR, and its state
* Sequence checklist: liquidity swept → displacement → MSS → FVG
* Setup direction, state, **quality score /100**, premium / discount location
* Entry, SL, TP1, TP2, TP3 and R:R
* **Market Story** — the sequence in chronological order with ✓ markers
* Optional detailed info panel (PDH/PDL, PWH/PWL, session levels, ATR, news window, MSS level,
  structure stop, risk in points, note)
* `CURRENT STATE` line

> **The score is a confluence score, NOT a probability of profit.** The panel says so explicitly.

---

## 6. Non-repainting

* Every `request.security()` call uses `barmerge.lookahead_off` **and** `barmerge.gaps_off`.
* Higher-timeframe swings use `ta.pivothigh()` / `ta.pivotlow()` inside the higher-timeframe
  context, so a swing is only known after its confirmation bars have **closed**.
* All state transitions run only on **confirmed bars** (`barstate.isconfirmed`). A developing sweep
  is shown as `POTENTIAL SWEEP` and only becomes `LIQUIDITY TAKEN` once the candle closes back
  through the level.
* Historical setups are drawn exactly as they were detectable at the time — nothing is re-coloured
  or back-filled with future data.

---

## 7. Alerts (one per event, no spam)

`Liquidity approaching` · `Liquidity swept` · `Bullish / bearish MSS` · `FVG created` ·
`Setup armed` · `Entry confirmed` · `TP1 / TP2 / TP3 reached` · `Setup invalidated`.

Each message contains symbol, timeframe, direction, entry, SL, TP1–TP3, R:R, quality and reason, e.g.

```
XAUUSD, 5 - LONG - Liquidity sweep + MSS + FVG confirmation | entry 3659.20 SL 3653.70
TP1 3668.40 TP2 3678.40 TP3 3684.70 | RR 1.68 / 3.51 / 4.66 | quality 85/100 | ASIA LOW
```

Anti-spam is structural: every alert is attached to a **one-way state transition** (a level is swept
once, a setup arms once, TP1 fires once, …).

---

## 8. News filter (honest implementation)

Pine Script has no reliable economic-calendar feed, so **nothing is invented**. The indicator ships a
**manual** `High Impact News Window`: you enter up to three event timestamps and the minutes
before/after; inside that window setups can be blocked (default) or penalised by `-20` quality
points.

---

## 9. Risk disclaimer

This indicator is a market-analysis and education tool. It does not place, simulate or guarantee any
trade, and "SETUP QUALITY: 85/100" is **not** an 85 % chance of profit. Suggested entries, stops and
targets are analytical suggestions only. Past structure does not predict future price. Use your own
risk management.

---

## 10. Repository layout

```
XAUUSD_Smart_Entry_Engine.pine        ← the indicator (single file, commented by section, 4-space indent)
XAUUSD_Smart_Entry_Engine.tabs.pine   ← identical code, tab indentation (paste fallback)
README.md                             ← this document
tools/tvline.py                       ← maps a TradingView error line/column back to a file line
tools/onestmt.py                      ← rewrites the file so every statement is on one physical line
tools/totabs.py                       ← regenerates the tab-indented copy
tools/verify.py                       ← static checks (indent, brackets, UDT arity, no strategy.*, …)
```

The three `tools/` scripts are the ones that were used to chase the compile errors reported by
TradingView; they are kept in the repo so the same checks can be re-run after any edit:

```
python3 tools/verify.py       # all invariants: indentation, brackets, UDT arity, indicator-only
python3 tools/onestmt.py XAUUSD_Smart_Entry_Engine.pine
python3 tools/totabs.py
python3 tools/tvline.py --token <token> --col <column>
```
