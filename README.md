# babymonster-dns-events

Source of truth for the TXT records at `_babymonster.paocloud.co.th`.

- `events.json` - concerts / releases / notes (schema enforced by `validate_events.py`)
- `validate_events.py` - strict validator; run before every merge and before the DNS server installs the file
- A weekly scheduled task (Sat 03:00 Asia/Bangkok) researches news, edits `events.json`, validates, opens a PR and merges it if validation passes
- The DNS server pulls `main` daily, validates again, then updates BIND via `nsupdate`

Rules for `events.json`: only `date` / `type` / `text`; type is `concert`, `release` or `note` (notes have no date); text max 60 chars, letters/digits/space and `( ) - . , / & + : ' #` only; no URLs.
