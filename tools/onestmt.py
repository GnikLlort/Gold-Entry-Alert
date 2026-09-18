#!/usr/bin/env python3
"""
onestmt.py - rewrite a Pine Script file so that every statement lives on ONE
physical line (no wrapped / continuation lines at all).

Why this exists
---------------
Pine's line-continuation rule is indentation based: a wrapped line must be
indented MORE than the first line of the statement it belongs to.  Any wrapped
line that sits at the same indent as its statement start produces

    Syntax error at input "end of line without line continuation"

and Pine stops at the first error, so one bad wrap hides everything after it.
Pasting through paths that normalise indentation makes the rule easy to break.
If no statement is ever wrapped, the whole error class disappears: the only
indentation the compiler has to read is block indentation (if / for / else /
function bodies), which is one tab (or four spaces) per level.

What it does
------------
Joins continuation lines onto their statement with a single space.  It is
conservative - it only joins a line when the accumulated statement is
syntactically incomplete:

  * unbalanced ( [ { , or
  * the line ends on an operator / comma / ternary ? or : / trailing dot

It also joins a line that *starts* with a token that can never begin a Pine
statement (`:`, `?`, `)`, `]`, `}`, `and`, `or`, `then`, `.`, ...) onto the
statement above it - that is the other way a wrapped line can hang.

It never joins:
  * comment-only or blank lines
  * `=>` function headers onto their body
  * block headers (if / else / for / while / type ...) onto their body

Safety checks are run before writing; the script aborts on any of:
  * a continuation line shallower than its statement start
  * a trailing `//` comment inside a wrapped statement
  * an unbalanced statement (bracket depth != 0 at the end of a group)

Usage:  python3 tools/onestmt.py FILE [-o OUTPUT]   (default: overwrite FILE)
"""
import argparse
import re
import sys

OPS = r"(?:\+\+|--|=>|==|!=|>=|<=|\?|:|,|\+|-|\*|/|%|>|<|=|\.|\band\b|\bor\b|\bnot\b)$"
OP_RE = re.compile(OPS)

# Tokens that can never begin a Pine statement -> a line starting with one of
# these is the tail of the statement above it.
BAD_START = re.compile(r"^(?::|\?|\)|\]|\}|=>|\band\b|\bor\b|\bthen\b|==|!=|>=|<=|=|\*|/|%|\.)")


def strip_code(line):
    """Code part of a line: drops a trailing // comment, keeps string bodies."""
    out = []
    i, n, instr = 0, len(line), None
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


def depth_delta(code):
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
        if c in "([{":
            d += 1
        elif c in ")]}":
            d -= 1
        i += 1
    return d


def trailing_op(code):
    t = code.rstrip()
    if not t or t.endswith("=>"):
        return None
    m = OP_RE.search(t)
    return m.group(0) if m else None


def next_code(lines, i):
    """Index of the next code line after i (skips blanks and comment lines)."""
    for j in range(i + 1, len(lines)):
        s = lines[j].strip()
        if s and not s.startswith("//"):
            return j
    return -1


def group(lines):
    """Split the file into logical statements. Returns list of line-index lists."""
    groups, cur = [], None
    for i, line in enumerate(lines):
        s = line.strip()
        if not s or s.startswith("//"):
            if cur:
                groups.append(cur)
                cur = None
            continue
        cur = [i] if cur is None else cur + [i]
        depth = sum(depth_delta(strip_code(lines[j])) for j in cur)
        nxt = next_code(lines, i)
        hangs = nxt >= 0 and BAD_START.match(lines[nxt].strip()) is not None
        if depth <= 0 and trailing_op(strip_code(line)) is None and not hangs:
            groups.append(cur)
            cur = None
    if cur:
        groups.append(cur)
    return groups


def indent_of(line):
    return len(line) - len(line.lstrip())


def join(lines, groups):
    out, index = [], 0
    for g in groups:
        while index < g[0]:                      # comments / blanks before it
            out.append(lines[index])
            index += 1
        out.append(" ".join([lines[g[0]].rstrip()] + [lines[j].strip() for j in g[1:]]))
        index = g[-1] + 1
    while index < len(lines):
        out.append(lines[index])
        index += 1
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("-o", "--out")
    a = ap.parse_args()

    src = open(a.path, encoding="utf-8").read()
    lines = src.split("\n")
    groups = group(lines)
    wrapped = [g for g in groups if len(g) > 1]

    problems = []
    for g in wrapped:
        base = indent_of(lines[g[0]])
        for j in g[1:]:
            if indent_of(lines[j]) < base:
                problems.append("line %d: continuation shallower than statement %d" % (j + 1, g[0] + 1))
            if lines[j].rstrip() != strip_code(lines[j]).rstrip():
                problems.append("line %d: trailing comment inside a wrapped statement" % (j + 1))
        if sum(depth_delta(strip_code(lines[j])) for j in g) != 0:
            problems.append("line %d: unbalanced brackets at end of statement" % (g[0] + 1))
    for g in wrapped[:-0]:
        for j in g[:-1]:
            if lines[j].rstrip() != strip_code(lines[j]).rstrip():
                problems.append("line %d: trailing comment inside a wrapped statement" % (j + 1))
    if problems:
        sys.exit("ABORT - refusing to rewrite:\n  " + "\n  ".join(problems))

    new = "\n".join(join(lines, groups))

    # post-conditions: one statement per line, nothing left hanging
    for i, l in enumerate(new.split("\n")):
        s = l.strip()
        if not s or s.startswith("//"):
            continue
        if BAD_START.match(s):
            sys.exit("ABORT - line %d still starts with a continuation token: %s" % (i + 1, l))
        if depth_delta(strip_code(l)) != 0:
            sys.exit("ABORT - line %d has unbalanced brackets: %s" % (i + 1, l))

    open(a.out or a.path, "w", encoding="utf-8").write(new)
    longest = max((len(l), i + 1) for i, l in enumerate(new.split("\n")))
    print("statements: %d   wrapped joined: %d   lines: %d -> %d   longest line: %d (line %d)"
          % (len(groups), len(wrapped), len(lines), len(new.split("\n")), longest[0], longest[1]))


if __name__ == "__main__":
    main()
