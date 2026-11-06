# Privacy

This repo and its website are public. The plan describes a real yard, so it takes some care to keep the people behind it out of it.

## What never goes in the repo

- Names of anyone in the household, neighbors, contractors or program staff. The copyright line and commits use the GitHub handle only.
- The street address, house number, parcel ID (PIN) or legal description. "Rochester, MN" is as specific as it gets.
- Email addresses (other than GitHub's noreply addresses), phone numbers, or account numbers.
- GPS coordinates, map pins, Street View links, or real-estate listing links.
- Photos with metadata. Phone photos embed GPS by default. Strip it (`exiftool -all= photo.jpg`), and check the picture itself for a visible house number, plates or faces.
- Office documents or PDFs. They embed the author's name. Use CSV, Markdown or JSON instead.
- Grant or permit applications. They require the owner's name and legal description, so keep them offline.

## How it's enforced

| Layer | What it does |
| --- | --- |
| `scripts/check_pii.py` | Scans for emails, phone numbers, street addresses, coordinates, parcel IDs, map and listing links, photo metadata and office files, plus a private denylist. It reports file and line only, never the matched text, so CI logs don't leak it either. |
| Git hooks (`.githooks/`) | Run the check on staged files, on commit messages, and on the author/committer of every commit you push. |
| CI (`.github/workflows/ci.yml`) | Runs the same check on every push and pull request, over all files and every commit in history. |
| Pages deploy (`.github/workflows/pages.yml`) | Publishes only `site/`, and only after the check passes. |
| The website | Loads nothing from other hosts. Its Content Security Policy blocks third-party scripts, fonts, trackers and embeds (maps, video). No cookies or analytics. Checklist ticks stay in the visitor's own browser. |

## One-time setup on each machine

```sh
git config core.hooksPath .githooks
git config user.email "<id>+<username>@users.noreply.github.com"
```

Then create a private denylist. It's gitignored, so it never leaves your machine:

```sh
printf '%s\n' "Your Name" "Your Street" "you@example.com" > .pii-denylist
```

For CI, put the same lines in a repository secret named `PII_DENYLIST` (Settings → Secrets and variables → Actions). On GitHub, also turn on **Settings → Emails → Keep my email addresses private** and **Block command line pushes that expose my email**.

## If something slips through

Deleting it in a new commit isn't enough, because it stays in history. Rewrite the history (for example `git filter-repo`), force-push, and ask GitHub Support to purge cached views of the old commits. Forks and clones made before the rewrite keep their copies.

## False positives

Add `pii-ok` anywhere on the line, ideally with a short reason.
