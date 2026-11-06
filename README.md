# Lawn & Order

A plan for turning a typical suburban front lawn in Rochester, MN (USDA zones 4b–5a) into something pollinator-friendly and low-maintenance, without breaking the bank. Three growing seasons, weekend-sized jobs, mostly free materials.

The short version: smother turf with cardboard and free city mulch, plant native plugs densely, keep a mown edge so it looks intentional, and lean on the bee lawn that's already there.

**Website: <https://jkastl.github.io/lawn-and-order/>.** It includes a to-scale site model, zone guide, bloom calendar, timeline checklist, budget calculator, the boulevard rules, and grant deadlines with countdowns. It works on phones.

## What's here

| Path | What it is |
| --- | --- |
| [`site/`](site/) | The website: static HTML, CSS and JS with no build step. Content lives in [`site/data/plan.json`](site/data/plan.json) and [`site/data/budget.json`](site/data/budget.json) |
| [`docs/conversion-plan.md`](docs/conversion-plan.md) | The full written plan: zones, plant lists, boulevard rules, timing, budget, open questions, sources |
| [`budget/budget.md`](budget/budget.md) | Budget summary and every line item, readable on GitHub |
| [`budget/budget.csv`](budget/budget.csv), [`budget/assumptions.csv`](budget/assumptions.csv) | The same budget as spreadsheet-friendly CSV |
| [`budget/build_budget.py`](budget/build_budget.py) | Regenerates the three budget files from `site/data/budget.json` |
| [`scripts/check_pii.py`](scripts/check_pii.py) | Privacy check that runs in git hooks and CI. See [PRIVACY.md](PRIVACY.md) |

## Working on it

Preview the site locally (it loads its JSON, so it needs a server rather than double-clicking the file):

```sh
python3 -m http.server -d site 8000
```

Then open <http://localhost:8000>.

To change the budget, edit `site/data/budget.json`, then regenerate the CSV and Markdown copies. CI fails if they're out of date.

```sh
python3 budget/build_budget.py
```

The site computes the same numbers in `site/budget.js`. If you change the math in one place, change it in the other.

Turn on the privacy hooks once per clone:

```sh
git config core.hooksPath .githooks
```

Pushes to `main` deploy `site/` to GitHub Pages once the privacy check passes. To set that up, go to **Settings → Pages → Build and deployment** and set the source to **GitHub Actions**.

## Caveats

- Dimensions are scaled from an aerial photo, roughly ±2–3 ft. Tape-measure before cutting bed edges.
- Prices and program details were checked in November 2026 and will drift. Each line carries its source.
- Bloom times on the website are typical for southern Minnesota and shift with the weather.
- Boulevard rules are Rochester-specific. Check your own city before planting in the right-of-way.
