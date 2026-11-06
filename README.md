# lawn-and-order

A plan for turning a typical suburban front lawn in Rochester, MN (USDA zones 4b–5a) into something pollinator-friendly and low-maintenance, without breaking the bank. Three growing seasons, weekend-sized jobs, mostly free materials.

The short version: smother turf with cardboard and free city mulch, plant native plugs densely, keep a mown edge so it looks intentional, and lean on the bee lawn that's already there.

## What's here

| Path | What it is |
| --- | --- |
| [`docs/conversion-plan.md`](docs/conversion-plan.md) | The full plan: zones, plant lists, boulevard rules, timing, budget, open questions |
| [`docs/site-baseline.md`](docs/site-baseline.md) | Condensed site reference: zone areas, light, phases, programs and deadlines |
| [`site-model/index.html`](site-model/index.html) | Interactive to-scale site model. Open it in a browser; click any zone for details. Views: Existing, Plan v1, Phases |
| [`budget/budget_generator.py`](budget/budget_generator.py) | Builds `Front_Yard_Budget.xlsx`: line items by phase, assumptions sheet, sources |

## Budget workbook

```sh
pip install openpyxl
cd budget
python budget_generator.py
```

Open the result in Excel or LibreOffice so the formulas calculate. Blue cells on the Assumptions sheet are inputs; yellow ones are the biggest cost drivers (plug price and planting density).

## Caveats

- Dimensions are scaled from an aerial photo, roughly ±2–3 ft. Tape-measure before cutting bed edges.
- Prices and program details were checked in November 2026 and will drift. Each line carries its source.
- Boulevard rules are Rochester-specific. Check your own city before planting in the right-of-way.
