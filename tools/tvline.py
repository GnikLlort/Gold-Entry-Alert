#!/usr/bin/env python3
"""Map TradingView editor line numbers <-> this repo's file line numbers.

TradingView strips blank lines, so its line N is the Nth NON-EMPTY line of the file.
Usage:  python3 tools/tvline.py 669            # TradingView line -> file line
        python3 tools/tvline.py -f 726         # file line -> TradingView line
        python3 tools/tvline.py 669 -c 3       # also show 3 lines of context
"""
import sys

TARGET = "XAUUSD_Smart_Entry_Engine.pine"

def build(path):
    with open(path, encoding="utf-8") as fh:
        lines = fh.read().split("\n")
    nonblank = [(i + 1, l) for i, l in enumerate(lines) if l.strip() != ""]
    return lines, nonblank

def main():
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    ctx = 0
    if "-c" in sys.argv:
        ctx = int(sys.argv[sys.argv.index("-c") + 1])
    from_file = "-f" in sys.argv
    if not args:
        print(__doc__); return
    n = int(args[0])
    lines, nonblank = build(TARGET)
    if from_file:
        tv = sum(1 for i, _ in nonblank if i <= n)
        print(f"file line {n}  ->  TradingView line {tv}")
        start = max(1, n - ctx)
        for i in range(start, min(len(lines), n + ctx)):
            print(f"  {i+1:5d}{'*' if i+1==n else ' '}| {lines[i]}")
    else:
        if n < 1 or n > len(nonblank):
            print(f"TradingView line {n} is out of range (file has {len(nonblank)} non-empty lines)")
            return
        file_line, text = nonblank[n - 1]
        print(f"TradingView line {n}  ->  file line {file_line}")
        if ctx:
            for i in range(max(1, file_line - ctx), min(len(lines), file_line + ctx)):
                print(f"  {i+1:5d}{'*' if i+1==file_line else ' '}| {lines[i]}")

if __name__ == "__main__":
    main()
