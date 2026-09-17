#!/usr/bin/env python3
"""
verify.py - static sanity checks for XAUUSD_Smart_Entry_Engine.pine.

These are the invariants the compiler kept tripping over while the file was
being written.  They are cheap to check locally and catch the mistakes before
TradingView has to (TradingView stops at the FIRST error, so every round trip
costs a paste).

Checked:
  1.  no tab characters                       (indentation must be 4 spaces)
  2.  no trailing whitespace / blank-ish lines
  3.  every indent is a multiple of 4
  4.  every line is bracket-balanced          (=> one statement per line)
  5.  no line starts with a continuation token (`:`, `?`, `)`, ... )
  6.  no block header without an indented body
  7.  no `strategy.` call outside a comment   (indicator only)
  8.  no `lookahead_on`                       (no repainting)
  9.  no type keyword inside a tuple declaration  (`[int a, float b] = ...`)
  10. UDT constructor calls pass the declared number of fields
  11. every `X.field` access uses a real field of that type
  12. every user function is defined before its first use
  13. the tabs copy is token-identical to the spaces copy

Usage:  python3 tools/verify.py [FILE] [TABS_FILE]
"""
import re
import sys

SPACE = sys.argv[1] if len(sys.argv) > 1 else "XAUUSD_Smart_Entry_Engine.pine"
TABS = sys.argv[2] if len(sys.argv) > 2 else "XAUUSD_Smart_Entry_Engine.tabs.pine"

src = open(SPACE, encoding="utf-8").read()
lines = src.split("\n")
fails = []


def chk(cond, msg):
    if cond:
        fails.append(msg)


def strip_code(line):
    """Drop a trailing // comment, keep string bodies intact."""
    out, i, n, instr = [], 0, len(line), None
    while i < n:
        c = line[i]
        if instr:
            if c == "\\":
                out.append(line[i:i + 2])
                i += 2
                continue
            out.append(c)
            if c == instr:
                instr = None
            i += 1
            continue
        if c in "\"'":
            instr = c
            out.append(c)
            i += 1
            continue
        if c == "/" and i + 1 < n and line[i + 1] == "/":
            break
        out.append(c)
        i += 1
    return "".join(out)


def depth(code):
    d, i, instr = 0, 0, None
    while i < len(code):
        c = code[i]
        if instr:
            if c == "\\":
                i += 2
                continue
            if c == instr:
                instr = None
            i += 1
            continue
        if c in "\"'":
            instr = c
            i += 1
            continue
        if c == "/" and i + 1 < len(code) and code[i + 1] == "/":
            break
        if c in "([{":
            d += 1
        elif c in ")]}":
            d -= 1
        i += 1
    return d


# 1 - 3  whitespace -----------------------------------------------------------
code_lines = [(i + 1, l) for i, l in enumerate(lines) if l.strip()]
chk(any("\t" in l for l in lines), "1. tab character present")
chk(any(l != l.rstrip() for l in lines), "2. trailing whitespace present")
for n, l in code_lines:
    ind = len(l) - len(l.lstrip())
    chk(ind % 4 != 0, "3. line %d indent %d is not a multiple of 4" % (n, ind))

# 4 - 5  one statement per line ----------------------------------------------
BAD_START = re.compile(r"^(?::|\?|\)|\]|\}|=>|\band\b|\bor\b|\bthen\b|==|!=|>=|<=|=|\*|/|%|\.)")
for n, l in code_lines:
    s = l.strip()
    if s.startswith("//"):
        continue
    chk(depth(strip_code(l)) != 0, "4. line %d is not bracket-balanced" % n)
    chk(BAD_START.match(s) is not None, "5. line %d starts with a continuation token" % n)

# 6  block headers need a body ------------------------------------------------
HEAD = re.compile(r"^\s*(if|else|for|while|switch)\b.*[^=>]\s*$|^[A-Za-z_]\w*\([^)]*\)\s*=>\s*$|^\s*=>\s*$")
for i, l in enumerate(lines):
    if not l.strip() or l.strip().startswith("//"):
        continue
    if HEAD.match(l) and not l.rstrip().endswith("=>"):
        if not (i + 1 < len(lines) and lines[i + 1].strip()
                and len(lines[i + 1]) - len(lines[i + 1].lstrip()) > len(l) - len(l.lstrip())):
            fails.append("6. line %d block header has no indented body: %s" % (i + 1, l.strip()[:60]))

# 7 - 8  indicator only / no repainting --------------------------------------
body = "\n".join(strip_code(l) for l in lines)
chk(re.search(r"\bstrategy\s*\.", body) is not None, "7. strategy.* call present")
chk("lookahead_on" in body, "8. lookahead_on present")
chk(not re.search(r"^\s*indicator\s*\(", src, re.M), "7b. no indicator() declaration found")

# 9  no typed tuple declarations ---------------------------------------------
chk(re.search(r"\[\s*(?:int|float|bool|string|color|line|box|label|table)\s+\w+\s*,", src) is not None,
    "9. type keyword inside a tuple declaration")

# 10 - 11  UDTs ---------------------------------------------------------------
types = {}
for m in re.finditer(r"^type\s+(\w+)\s*\n((?:\s+\w+\s+\w+.*\n)+)", src, re.M):
    name = m.group(1)
    fields = re.findall(r"^\s*(\w+)\s+(\w+)\s*(?://.*)?$", m.group(2), re.M)
    types[name] = [f[1] for f in fields]
chk(not types, "10. no UDT definitions found (%d)" % len(types))
for t, fl in types.items():
    for m in re.finditer(r"\b%s\.new\(" % t, body):
        # count top-level commas in the call
        i = m.end()
        d, args, cur = 1, 0, ""
        while d:
            c = body[i]
            if c in "\"'":
                j = body.index(c, i + 1)
                cur += body[i:j + 1]
                i = j
            elif c in "([{":
                d += 1
            elif c in ")]}":
                d -= 1
                if d == 0:
                    break
            elif c == "," and d == 1:
                args += 1
            i += 1
        nargs = args + 1 if cur.strip() or args else 0
        chk(nargs != len(fl), "10. %s.new() called with %d args, type has %d fields"
            % (t, nargs, len(fl)))
for m in re.finditer(r"\b([A-Z]\w*)\.(\w+)\b", body):
    t, f = m.group(1), m.group(2)
    if t in types and f not in types[t] and f != "new":
        chk(True, "11. %s.%s is not a field of type %s" % (t, f, t))

# 12  functions defined before use -------------------------------------------
defs = {}
for i, l in enumerate(lines):
    m = re.match(r"^(\w+)\s*\(", l)
    if m and l.rstrip().endswith("=>"):
        defs.setdefault(m.group(1), i + 1)
for fn, ln in defs.items():
    for i, l in enumerate(lines):
        if re.search(r"\b%s\s*\(" % fn, l) and (i + 1) not in (ln,):
            chk(i + 1 < ln and not l.strip().startswith("//"),
                "12. %s() used on line %d but defined on line %d" % (fn, i + 1, ln))
            break

# 13  tabs copy identical -----------------------------------------------------
try:
    tabs = open(TABS, encoding="utf-8").read().split("\n")
    tok = lambda ls: [re.sub(r"\s+", " ", l).strip() for l in ls if l.strip()]
    a, b = tok(lines), tok(tabs)
    chk(a != b, "13. tabs copy differs from the spaces copy")
    if a != b:
        for i, (x, y) in enumerate(zip(a, b)):
            if x != y:
                fails.append("    first difference at token line %d:\n      %s\n      %s" % (i + 1, x, y))
                break
except FileNotFoundError:
    print("note: %s not found - skipped check 13" % TABS)

print("checked %d lines, %d UDTs (%s), %d functions"
      % (len(lines), len(types), ", ".join("%s:%d" % (k, len(v)) for k, v in types.items()), len(defs)))
if fails:
    seen, uniq = set(), []
    for f in fails:
        if f not in seen:
            seen.add(f)
            uniq.append(f)
    print("FAIL (%d):" % len(uniq))
    for f in uniq[:40]:
        print("  -", f)
    sys.exit(1)
print("OK - all checks passed")
