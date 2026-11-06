#!/usr/bin/env python3
"""Block personally identifiable information from entering this public repo.

Checks file contents, binary metadata and commit metadata for things that
should never be published: email addresses, phone numbers, street addresses,
GPS coordinates, parcel IDs, map/real-estate links, photos with EXIF, office
documents (which embed author names), plus any term on a private denylist.

Findings are reported by file, line and kind only. The matched text is never
printed, because CI logs on a public repo are public too.

Usage:
  scripts/check_pii.py                 scan every tracked file (default)
  scripts/check_pii.py --staged        scan what's staged (pre-commit hook)
  scripts/check_pii.py --message FILE  scan a commit message (commit-msg hook)
  scripts/check_pii.py --commits [REV] check author/committer/trailers of every
                                       commit reachable from REV (default HEAD)
  scripts/check_pii.py --history       scan every file version in git history

Private denylist (names, your street, your email, ...), one term per line,
case-insensitive, '#' for comments. Never commit it:
  - local:  .pii-denylist in the repo root (gitignored)
  - CI:     the PII_DENYLIST repository secret (newline-separated)

To accept a false positive, put `pii-ok` on the same line.
Standard library only.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

ALLOWED_EMAIL = re.compile(
    r"(?:^|@)(?:users\.noreply\.github\.com|example\.(?:com|org|net))$"
    r"|^(?:noreply@github\.com|noreply@anthropic\.com)$",
    re.I,
)
ALLOWED_COMMIT_EMAIL = re.compile(
    r"^(?:\d+\+)?[A-Za-z0-9-]+(?:\[bot\])?@users\.noreply\.github\.com$|^noreply@(?:github|anthropic)\.com$",
    re.I,
)

STREET_SUFFIX = (r"St|Street|Ave|Avenue|Rd|Road|Dr|Drive|Ln|Lane|Ct|Court|Pl|Place|Blvd|Way|Cir|Circle|"
                 r"Pkwy|Parkway|Ter|Terrace|Trl|Trail|Hwy|Highway|Sq|Loop|Run|Pt|Point")
PATTERNS = [
    ("email address", re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}")),
    ("phone number", re.compile(r"(?<![\d.])(?:\+?1[-. ]?)?\(?\d{3}\)?[-. ]\d{3}[-. ]\d{4}(?![\d.])")),
    ("street address", re.compile(
        rf"\b\d{{1,6}}(?:\s+[NSEW]\.?)?(?:\s+(?:\d+(?:st|nd|rd|th)|[A-Z][a-z]+)){{1,3}}\s+(?:{STREET_SUFFIX})\b\.?"
        r"(?:\s+(?:NW|NE|SW|SE))?")),
    ("street address (quadrant)", re.compile(r"\b\d{1,6}\s+\S+(?:\s+\S+)?\s+(?:NW|NE|SW|SE)\b")),
    ("GPS coordinates", re.compile(r"-?\b\d{1,2}\.\d{4,}\s*,\s*-?\d{1,3}\.\d{4,}\b")),
    ("parcel ID", re.compile(r"\b\d{2}\.\d{2}\.\d{2}\.\d{6}\b")),
    ("SSN-like number", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
    ("map or listing link", re.compile(
        r"(?:google\.[a-z.]+/maps|maps\.google\.|maps\.app\.goo\.gl|goo\.gl/maps|bing\.com/maps|"
        r"openstreetmap\.org/[^\s)]*#map=|maps\.apple\.com|zillow\.com|redfin\.com|realtor\.com|trulia\.com|"
        r"what3words\.com|w3w\.co)", re.I)),
]

BLOCKED_EXT = {".xlsx", ".xlsm", ".xls", ".docx", ".doc", ".pptx", ".ppt", ".odt", ".ods", ".odp",
               ".pdf", ".heic", ".heif", ".dng", ".cr2", ".nef", ".mov", ".mp4", ".kml", ".kmz", ".gpx"}
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff", ".gif", ".avif"}
IMAGE_META = [b"Exif\x00\x00", b"eXIf", b"<x:xmpmeta", b"GPSLatitude", b"tEXtAuthor", b"iTXtAuthor"]
SKIP = {".pii-denylist"}


def load_denylist() -> list[str]:
    terms: list[str] = []
    f = ROOT / ".pii-denylist"
    sources = [f.read_text(encoding="utf-8")] if f.exists() else []
    sources.append(os.environ.get("PII_DENYLIST", ""))
    for src in sources:
        for line in src.splitlines():
            line = line.strip()
            if line and not line.startswith("#") and len(line) >= 3:
                terms.append(line.lower())
    return terms


DENY = load_denylist()


def git(*args: str, binary: bool = False):
    out = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, check=True).stdout
    return out if binary else out.decode("utf-8", "replace")


def scan_text(name: str, text: str) -> list[str]:
    found = []
    for i, line in enumerate(text.splitlines(), 1):
        if "pii-ok" in line:
            continue
        low = line.lower()
        for t in DENY:
            if t in low:
                found.append(f"{name}:{i}: matches a private denylist entry")
                break
        for kind, rx in PATTERNS:
            for m in rx.finditer(line):
                if kind == "email address" and ALLOWED_EMAIL.search(m.group(0)):
                    continue
                found.append(f"{name}:{i}: possible {kind}")
                break
    return found


def scan_blob(name: str, data: bytes) -> list[str]:
    if name in SKIP:
        return []
    ext = Path(name).suffix.lower()
    if ext in BLOCKED_EXT:
        return [f"{name}: {ext} files can carry author names, GPS or hidden text. Export to CSV, Markdown or a stripped image instead"]
    found = []
    if ext in IMAGE_EXT:
        if any(sig in data for sig in IMAGE_META):
            found.append(f"{name}: image has EXIF/XMP/text metadata (may include GPS or camera owner). Strip it first, e.g. `exiftool -all= file`")
        low = data.lower()
        found += [f"{name}: image metadata matches a private denylist entry" for t in DENY if t.encode() in low][:1]
        return found
    if b"\x00" in data[:8000]:
        return [f"{name}: unrecognized binary file; can't verify it's free of personal data"]
    return scan_text(name, data.decode("utf-8", "replace"))


def tracked_files() -> list[str]:
    return [p for p in git("ls-files", "-z").split("\0") if p]


def mode_all() -> list[str]:
    found = []
    for p in tracked_files():
        fp = ROOT / p
        if fp.is_file():
            found += scan_blob(p, fp.read_bytes())
    return found


def mode_staged() -> list[str]:
    found = []
    names = [p for p in git("diff", "--cached", "--name-only", "-z", "--diff-filter=ACMR").split("\0") if p]
    for p in names:
        found += scan_blob(p, git("show", f":{p}", binary=True))
    return found


def mode_history() -> list[str]:
    found, seen = [], set()
    for line in git("rev-list", "--objects", "--all").splitlines():
        parts = line.split(" ", 1)
        if len(parts) != 2 or parts[0] in seen:
            continue
        sha, path = parts
        if git("cat-file", "-t", sha).strip() != "blob":
            continue
        seen.add(sha)
        found += [f"(history {sha[:8]}) {f}" for f in scan_blob(path, git("cat-file", "blob", sha, binary=True))]
    return found


def check_message(label: str, msg: str) -> list[str]:
    found = []
    for i, line in enumerate(msg.splitlines(), 1):
        if line.startswith("#"):
            continue
        m = re.match(r"\s*(?:Co-authored-by|Signed-off-by|Reviewed-by|Reported-by):\s*.*<([^>]+)>", line, re.I)
        if m and not ALLOWED_COMMIT_EMAIL.match(m.group(1)):
            found.append(f"{label} line {i}: trailer uses a non-noreply email")
            continue
        found += [f.replace("<msg>:", f"{label} line ") for f in scan_text("<msg>", line)]
    return found


def mode_commits(rev: str) -> list[str]:
    found = []
    fmt = "%H%x1f%an%x1f%ae%x1f%cn%x1f%ce%x1f%B%x1e"
    for rec in git("log", rev, f"--format={fmt}").split("\x1e"):
        rec = rec.strip("\n")
        if not rec:
            continue
        sha, an, ae, cn, ce, body = rec.split("\x1f", 5)
        tag = f"commit {sha[:8]}"
        for role, name, email in (("author", an, ae), ("committer", cn, ce)):
            if not ALLOWED_COMMIT_EMAIL.match(email):
                found.append(f"{tag}: {role} email isn't a GitHub noreply address")
            if any(t in name.lower() for t in DENY):
                found.append(f"{tag}: {role} name matches a private denylist entry")
        found += check_message(tag, body)
    return found


def main(argv: list[str]) -> int:
    if "--staged" in argv:
        found = mode_staged()
    elif "--message" in argv:
        f = argv[argv.index("--message") + 1]
        found = check_message("commit message", Path(f).read_text(encoding="utf-8", errors="replace"))
    elif "--commits" in argv:
        i = argv.index("--commits")
        rev = argv[i + 1] if i + 1 < len(argv) and not argv[i + 1].startswith("-") else "HEAD"
        found = mode_commits(rev)
    elif "--history" in argv:
        found = mode_history()
    else:
        found = mode_all()
    if "--all" in argv and "--commits" in argv:
        found = mode_all() + found
    if found:
        print("Privacy check failed. Nothing personal should be published in this repo:\n")
        print("\n".join("  " + f for f in sorted(set(found))))
        print("\nRemove it, or add `pii-ok` to the line if it's a false positive. See PRIVACY.md.")
        return 1
    print(f"Privacy check passed ({'with' if DENY else 'without'} a private denylist).")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
