#!/usr/bin/env python3
"""Keep the version in step everywhere it appears.

VERSION is the single source. This fails if it isn't valid semver, if
CHANGELOG.md has no "## [X.Y.Z]" section for it, or if the site footer
shows a different version.

Usage:
  python3 scripts/check_version.py           # check (CI)
  python3 scripts/check_version.py --notes   # print this version's changelog section
Standard library only.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$")


def version() -> str:
    return (ROOT / "VERSION").read_text(encoding="utf-8").strip()


def notes(v: str) -> str:
    text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    m = re.search(rf"^## \[{re.escape(v)}\][^\n]*\n(.*?)(?=^## \[|^\[[^\]]+\]: |\Z)", text, re.M | re.S)
    return m.group(1).strip() if m else ""


def main() -> int:
    v = version()
    if "--notes" in sys.argv:
        print(notes(v))
        return 0
    errors = []
    if not SEMVER.match(v):
        errors.append(f"VERSION '{v}' isn't semantic versioning (X.Y.Z)")
    if not notes(v):
        errors.append(f"CHANGELOG.md has no '## [{v}]' section with notes")
    html = (ROOT / "site" / "index.html").read_text(encoding="utf-8")
    m = re.search(r"data-version>v([^<]+)<", html)
    if not m:
        errors.append("site/index.html footer has no data-version link")
    elif m.group(1) != v:
        errors.append(f"site/index.html footer shows v{m.group(1)}, VERSION is {v}")
    if errors:
        print("Version check failed:\n" + "\n".join("  " + e for e in errors))
        return 1
    print(f"Version {v} is consistent.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
