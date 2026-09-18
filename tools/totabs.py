#!/usr/bin/env python3
"""
totabs.py - write a tab-indented copy of the Pine file.

Pine blocks are indentation based.  The main file uses 4 spaces per level, but
some paste paths (chat windows, some browsers, some editors) collapse runs of
spaces, which destroys the block structure and the script stops compiling.
Tabs survive those paths, so a tab-indented twin of the file is shipped next to
it: same code, one tab per level.

Only LEADING whitespace is converted - alignment spaces inside a line (the
column padding in the input block, for example) are left untouched.

Usage:  python3 tools/totabs.py [FILE] [OUTPUT]
"""
import sys

src_path = sys.argv[1] if len(sys.argv) > 1 else "XAUUSD_Smart_Entry_Engine.pine"
out_path = sys.argv[2] if len(sys.argv) > 2 else "XAUUSD_Smart_Entry_Engine.tabs.pine"

lines = open(src_path, encoding="utf-8").read().split("\n")
out, bad = [], []
for n, l in enumerate(lines, 1):
    if not l.strip():
        out.append("")
        continue
    ind = len(l) - len(l.lstrip())
    if ind % 4:
        bad.append(n)
    out.append("\t" * (ind // 4) + l[ind:])

if bad:
    sys.exit("ABORT - indent not a multiple of 4 on lines: %s" % bad[:20])

open(out_path, "w", encoding="utf-8").write("\n".join(out))
print("%s -> %s  (%d lines, max level %d)"
      % (src_path, out_path, len(out), max((len(l) - len(l.lstrip(" \t"))) for l in out if l.strip())))
