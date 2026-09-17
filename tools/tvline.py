#!/usr/bin/env python3
"""Locate a TradingView compile error inside XAUUSD_Smart_Entry_Engine.pine.

TradingView strips blank lines (and its numbering does not map 1:1 to this file),
so the line NUMBER is unreliable - the token and column are not. This tool tries
several numbering rules and can also search by token.

Usage:
    python3 tools/tvline.py 669                 # show candidate lines for TV line 669
    python3 tools/tvline.py 669 6               # ... restricted to column 6
    python3 tools/tvline.py --token b1          # find every line containing 'b1'
    python3 tools/tvline.py --token b1 --col 6  # ... where 'b1' starts at column 6
"""
import re, sys

TARGET = "XAUUSD_Smart_Entry_Engine.pine"

def strip_comments(line):
    out = []; i = 0; instr = False
    while i < len(line):
        c = line[i]
        if instr:
            out.append(c)
            if c == "\\":
                if i + 1 < len(line): out.append(line[i + 1])
                i += 2; continue
            if c == '"': instr = False
            i += 1; continue
        if c == '"': instr = True; out.append(c); i += 1; continue
        if c == "/" and i + 1 < len(line) and line[i + 1] == "/": break
        out.append(c); i += 1
    return "".join(out)

def main():
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    token = sys.argv[sys.argv.index("--token") + 1] if "--token" in sys.argv else None
    col = int(sys.argv[sys.argv.index("--col") + 1]) if "--col" in sys.argv else None

    with open(TARGET, encoding="utf-8") as fh:
        lines = fh.read().split("\n")

    if token:
        print(f'lines where "{token}" starts at column {col if col else "any"}:')
        for i, l in enumerate(lines, 1):
            if token in strip_comments(l):
                c = strip_comments(l).find(token) + 1
                if col is None or c == col:
                    print(f"  file {i:5d} (col {c:3d}) | {l.strip()[:100]}")
        return

    n = int(args[0])
    if len(args) > 1 and col is None:
        col = int(args[1])

    rules = {
        "raw (nothing stripped)": [l for l in lines],
        "blank lines stripped": [l for l in lines if l.strip() != ""],
        "blank + comment lines stripped": [l for l in lines if strip_comments(l).strip() != ""],
    }
    print(f"candidates for TradingView line {n}" + (f", column {col}" if col else "") + ":")
    for name, subset in rules.items():
        if 1 <= n <= len(subset):
            text = subset[n - 1]
            ok = "" if col is None else ("  <-- column matches" if len(text) - len(text.lstrip()) < col <= len(text) else "")
            print(f"  [{name:32s}] {text.strip()[:95]}{ok}")
        else:
            print(f"  [{name:32s}] out of range ({len(subset)} lines)")
    print("\ntip: the token+column is the reliable clue, e.g.  python3 tools/tvline.py --token b1 --col 6")

if __name__ == "__main__":
    main()
