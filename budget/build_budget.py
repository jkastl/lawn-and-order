#!/usr/bin/env python3
"""Build the budget tables from site/data/budget.json.

Writes, next to this script:
  budget.csv       one row per line item, with low/high totals
  assumptions.csv  every input the totals depend on, with sources
  budget.md        phase summary + line items, readable on GitHub

The JSON file is the single source of truth. The website computes the same
numbers live in the browser (site/budget.js), so if you change the math here,
change it there too.

Usage:
  python3 budget/build_budget.py          # regenerate the files
  python3 budget/build_budget.py --check  # exit 1 if the files are stale (CI)

Standard library only; no installs needed.
"""
from __future__ import annotations

import csv
import io
import json
import sys
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "site" / "data" / "budget.json"


def rnd(x: float, places: int = 0) -> float:
    """Round half away from zero, like Excel and JavaScript (for positives)."""
    q = Decimal(1).scaleb(-places)
    return float(Decimal(repr(x)).quantize(q, rounding=ROUND_HALF_UP))


def compute(data: dict, include_optional: bool = True) -> list[dict]:
    a = {r["key"]: r["value"] for r in data["assumptions"] if "key" in r}
    rows = []
    required_plugs = 0.0
    for it in data["items"]:
        q = it["qty"]
        if "fixed" in q:
            qty = float(q["fixed"])
        elif "plugs" in q:
            qty = rnd(a[q["plugs"]] * a["plugDensity"])
        elif "mulch" in q:
            qty = rnd(a[q["mulch"]] * a["mulchDepth"] / 12 / 27, 1)
        elif "seed" in q:
            qty = rnd(a[q["seed"]] / 1000 * a["seedRate"], 1)
        elif q.get("replacement"):
            qty = rnd(required_plugs * a["replacementPct"])
        else:
            raise ValueError(f"unknown qty spec: {q}")
        if it["unit"] == "plugs" and not it["optional"] and not q.get("replacement"):
            required_plugs += qty
        lo, hi = (a[p] if isinstance(p, str) else p for p in it["price"])
        rows.append({**it, "qtyValue": qty, "lo": lo, "hi": hi, "totalLo": qty * lo, "totalHi": qty * hi})
    return rows


def money(x: float) -> str:
    return f"${rnd(x):,.0f}"


def num(x: float) -> str:
    return f"{x:,.0f}" if x == int(x) else f"{x:,.1f}"


def build(data: dict) -> dict[str, str]:
    rows = compute(data)
    a = {r["key"]: r["value"] for r in data["assumptions"] if "key" in r}

    # budget.csv
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["phase", "when", "item", "qty", "unit", "unit_low", "unit_high", "total_low", "total_high", "optional", "note"])
    for r in rows:
        w.writerow([r["phase"], r["when"], r["item"], num(r["qtyValue"]), r["unit"],
                    f"{r['lo']:.2f}", f"{r['hi']:.2f}", f"{r['totalLo']:.2f}", f"{r['totalHi']:.2f}",
                    "yes" if r["optional"] else "no", r["note"]])
    budget_csv = buf.getvalue()

    # assumptions.csv
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["group", "key", "label", "value", "unit", "source"])
    group = ""
    for r in data["assumptions"]:
        if "group" in r:
            group = r["group"]
            continue
        w.writerow([group, r["key"], r["label"], r["value"], r["unit"], r["source"]])
    assumptions_csv = buf.getvalue()

    # budget.md
    out = ["# Front yard budget", "",
           f"_Generated from [`site/data/budget.json`](../site/data/budget.json) by `budget/build_budget.py`. "
           f"Prices as of {data['asOf']}. Don't edit by hand._", "",
           data["note"], "", "## Summary by phase", "",
           "| Phase | Timing | Base plan | Optional extras |", "| --- | --- | --- | --- |"]
    tot = {"lo": 0.0, "hi": 0.0, "olo": 0.0, "ohi": 0.0}
    for p in data["phases"]:
        req = [r for r in rows if r["phase"] == p["phase"] and not r["optional"]]
        opt = [r for r in rows if r["phase"] == p["phase"] and r["optional"]]
        lo, hi = sum(r["totalLo"] for r in req), sum(r["totalHi"] for r in req)
        olo, ohi = sum(r["totalLo"] for r in opt), sum(r["totalHi"] for r in opt)
        tot["lo"] += lo; tot["hi"] += hi; tot["olo"] += olo; tot["ohi"] += ohi
        out.append(f"| {p['phase']}: {p['title']} | {p['timing']} | {money(lo)}–{money(hi)} | {money(olo)}–{money(ohi)} |")
    out.append(f"| **Total** |  | **{money(tot['lo'])}–{money(tot['hi'])}** | **{money(tot['olo'])}–{money(tot['ohi'])}** |")
    grants = a["grantL2L"] + a["grantGarden"]
    plugs = sum(r["qtyValue"] for r in rows if r["unit"] == "plugs" and not r["optional"])
    mulch = sum(r["qtyValue"] for r in rows if r["unit"] == "cu yd")
    out += ["",
            f"Net of grants entered in the assumptions ({money(grants)}): "
            f"**{money(max(0, tot['lo'] - grants))}–{money(max(0, tot['hi'] - grants))}** for the base plan.", "",
            f"Plugs needed (base plan): **{num(plugs)}**. Mulch and topsoil, all lines: **{num(mulch)} cu yd**.", "",
            "## Line items", "",
            "| Phase | When | Item | Qty | Unit $ | Total | Optional | Note |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for r in rows:
        unit = f"${r['lo']:.2f}–${r['hi']:.2f}" if r["lo"] != r["hi"] else f"${r['lo']:.2f}"
        out.append(f"| {r['phase']} | {r['when']} | {r['item']} | {num(r['qtyValue'])} {r['unit']} | {unit} | "
                   f"{money(r['totalLo'])}–{money(r['totalHi'])} | {'yes' if r['optional'] else ''} | {r['note']} |")
    out += ["", "## Assumptions", "", "| Input | Value | Source |", "| --- | --- | --- |"]
    for r in data["assumptions"]:
        if "group" in r:
            out.append(f"| **{r['group']}** | | |")
        else:
            out.append(f"| {r['label']} ({r['unit']}) | {r['value']} | {r['source']} |")
    out += ["", "## Sources", ""]
    for s in data["sources"]:
        out.append(f"- [{s['label']}]({s['url']})" if s["url"] else f"- {s['label']}")
    return {"budget.csv": budget_csv, "assumptions.csv": assumptions_csv, "budget.md": "\n".join(out) + "\n"}


def main() -> int:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    files = build(data)
    if "--check" in sys.argv:
        stale = [n for n, body in files.items()
                 if not (HERE / n).exists() or (HERE / n).read_text(encoding="utf-8") != body]
        if stale:
            print("Out of date: " + ", ".join(f"budget/{n}" for n in stale))
            print("Run: python3 budget/build_budget.py")
            return 1
        print("Budget files are up to date.")
        return 0
    for name, body in files.items():
        (HERE / name).write_text(body, encoding="utf-8")
        print(f"wrote budget/{name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
