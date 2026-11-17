#!/usr/bin/env python3
"""Strict validator for events.json. Exit 0 = OK, exit 1 = rejected (reasons on stderr).

Used both by the weekly AI task (before it merges) and by the DNS server (before it installs the file).
Everything that ends up in a DNS TXT record must pass this, so web-scraped text can't smuggle anything in.
"""
import json
import re
import sys
from datetime import date, datetime

TYPES = {"concert", "release", "note"}
MAX_EVENTS = 80
MAX_TEXT = 60
TEXT_RE = re.compile(r"^[A-Za-z0-9 ()\-.,/&+:'#]+$")   # no quotes, backslash, semicolon, <>, etc.
BAD_WORDS = re.compile(r"(https?:|www\.|ignore|instruction|system|prompt|password|secret|token)", re.I)
MIN_DATE, MAX_DATE = date(2026, 1, 1), date(2028, 12, 31)


def validate(path):
    errs = []
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:  # noqa: BLE001
        return [f"cannot parse JSON: {e}"]

    if not isinstance(data, list):
        return ["top level must be a list"]
    if not 1 <= len(data) <= MAX_EVENTS:
        errs.append(f"event count {len(data)} outside 1..{MAX_EVENTS}")

    seen = set()
    for i, e in enumerate(data):
        where = f"#{i}"
        if not isinstance(e, dict) or set(e) - {"date", "type", "text"}:
            errs.append(f"{where}: must be an object with only date/type/text")
            continue
        t = e.get("type")
        if t not in TYPES:
            errs.append(f"{where}: bad type {t!r}")
        text = e.get("text")
        if not isinstance(text, str) or not text.strip():
            errs.append(f"{where}: missing text")
        else:
            if len(text) > MAX_TEXT:
                errs.append(f"{where}: text longer than {MAX_TEXT}")
            if not TEXT_RE.match(text):
                errs.append(f"{where}: text has disallowed characters")
            if BAD_WORDS.search(text):
                errs.append(f"{where}: text contains a disallowed word/URL")
        d = e.get("date")
        if t == "note":
            if d is not None:
                errs.append(f"{where}: note must not have a date")
        else:
            try:
                dd = datetime.strptime(d, "%Y-%m-%d").date()
                if not MIN_DATE <= dd <= MAX_DATE:
                    errs.append(f"{where}: date {d} out of range")
            except Exception:  # noqa: BLE001
                errs.append(f"{where}: bad date {d!r}")
        key = (d, t, text)
        if key in seen:
            errs.append(f"{where}: duplicate")
        seen.add(key)
    return errs


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: validate_events.py events.json")
    problems = validate(sys.argv[1])
    if problems:
        print("REJECTED:\n  " + "\n  ".join(problems), file=sys.stderr)
        sys.exit(1)
    print("OK")
