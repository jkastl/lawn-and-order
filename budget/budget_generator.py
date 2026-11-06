"""Build Front_Yard_Budget.xlsx: assumptions, line-item budget, phase summary, sources.

Usage: pip install openpyxl && python budget_generator.py
Open the result in Excel or LibreOffice so the formulas calculate.
"""
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

wb = Workbook()
F = "Arial"
blue = Font(name=F, color="0000FF"); black = Font(name=F); green = Font(name=F, color="008000")
bold = Font(name=F, bold=True); hdr = Font(name=F, bold=True, color="FFFFFF")
title = Font(name=F, bold=True, size=14); note = Font(name=F, italic=True, color="666666", size=9)
hfill = PatternFill("solid", fgColor="3F5F3F"); yellow = PatternFill("solid", fgColor="FFFF00")
band = PatternFill("solid", fgColor="E8EFE8")
thin = Side(style="thin", color="BBBBBB"); top = Border(top=Side(style="thin", color="000000"))
USD = '$#,##0;($#,##0);-'; USD2 = '$#,##0.00;($#,##0.00);-'

# ---------------- Assumptions ----------------
A = wb.active; A.title = "Assumptions"
A["A1"] = "Assumptions (blue = edit me; yellow = biggest cost drivers)"; A["A1"].font = title
A["A2"] = "Areas are scaled from an aerial photo (±2–3 ft); tape-measure and update. Prices checked Nov 2026 unless marked 'estimate'."; A["A2"].font = note
rows = [
 ("Prices", None, None, None),
 ("Plug price, low ($/plug)", 1.97, USD2, "New Leaf Natives 38-plug single-species tray $75 = $1.97/plug (Olmsted SWCD 2026 kit: $80/36 = $2.22)"),
 ("Plug price, high ($/plug)", 2.75, USD2, "Estimate: smaller quantities / pricier species (e.g., Prairie Phlox tray $105 = $2.76)"),
 ("Native shrub, low ($/each)", 25, USD, "Estimate, unverified: 1-gal native shrub at a local nursery"),
 ("Native shrub, high ($/each)", 45, USD, "Estimate, unverified: 2–3 gal native shrub"),
 ("Bee lawn seed, low ($/lb)", 17.50, USD2, "Nokomis East 1-lb bag $17.50 (UMN mix)"),
 ("Bee lawn seed, high ($/lb)", 30, USD2, "Mann Lake bee lawn mix, from $29.99"),
 ("Core aerator rental, low ($)", 60, USD, "Typical 4-hr rental ~$60–$83"),
 ("Core aerator rental, high ($)", 90, USD, "Typical full-day rental ~$90–$116"),
 ("Free mulch/topsoil donation, low ($/cu yd)", 0, USD, "City giveaway: free, donation requested"),
 ("Free mulch/topsoil donation, high ($/cu yd)", 10, USD, "Guess at a reasonable donation; edit to taste"),
 ("Rates", None, None, None),
 ("Plugs per sq ft (15–18 in. spacing)", 0.6, '0.00', "15 in. grid = 0.64/sq ft; 18 in. = 0.44/sq ft"),
 ("Smother mulch depth (in.)", 4, '0', "Over cardboard"),
 ("Bee lawn seeding rate (lb per 1,000 sq ft)", 5, '0.0', "UMN mix label rate; overseeding can go 2–4 lb"),
 ("Replacement allowance (% of plugs)", 0.10, '0%', "Estimate for losses in year 1"),
 ("Areas (sq ft)", None, None, None),
 ("Phase 1: corner bed to plant (new 165 + gaps in existing)", 250, '#,##0', "Z2 + south of wing"),
 ("Phase 1: stump island bed (Z3 expanded around T1 stump)", 100, '#,##0', "Foundation bed widened west to wrap the stump; verify stump location"),
 ("Phase 1: new area to smother", 265, '#,##0', "Z2 extension 165 + stump island 100"),
 ("Phase 2: shade bed area for plugs (after shrubs)", 330, '#,##0', "Z4 ~450 sq ft minus ~120 sq ft under 3 shrubs"),
 ("Phase 2: area to smother (Z4 + south border)", 640, '#,##0', "Z4 450 + border 190"),
 ("Boulevard bee lawn area (Option A)", 265, '#,##0', "Boulevard south of the drive; the open front lawn is already mostly bee lawn"),
 ("Existing bee lawn to touch up (open lawn)", 790, '#,##0', "Z1 ~730 + 2 ft fence strip ~60"),
 ("Phase 3: south border bed", 190, '#,##0', "Z1 south border, minus a 2 ft access strip along the neighbor's fence"),
 ("Phase 3: boulevard core (Option B)", 152, '#,##0', "~4 ft wide after 18 in. setbacks × ~38 ft"),
 ("Grant", None, None, None),
 ("Lawns to Legumes reimbursement (if awarded)", 400, USD, "Up to $400; apply by Nov 30, 2026; set to 0 if not awarded"),
 ("Rochester Garden Grant (if awarded)", 0, USD, "Up to $1,000, 25% match, apply Oct 1–Dec 31 for 2027; enter the award here. Ask both programs whether they can stack"),
 ("Rain barrel", None, None, None),
 ("Rain barrel, low ($)", 70, USD, "County/RAM truckload sales elsewhere run ~$61–$70 (Livingston Co. MI 2026: $69.95)"),
 ("Rain barrel, high ($)", 130, USD, "Estimate, unverified: retail 50–60 gal barrel"),
 ("Diverter + overflow hose, low ($)", 20, USD, "Estimate, unverified"),
 ("Diverter + overflow hose, high ($)", 40, USD, "Estimate, unverified"),
]
r = 4; ref = {}
A["A3"], A["B3"], A["C3"] = "Input", "Value", "Source / note"
for c in "ABC": A[f"{c}3"].font = hdr; A[f"{c}3"].fill = hfill
for label, val, fmt, src in rows:
    A[f"A{r}"] = label
    if val is None:
        A[f"A{r}"].font = bold; A[f"A{r}"].fill = band; A[f"B{r}"].fill = band; A[f"C{r}"].fill = band
    else:
        A[f"A{r}"].font = black
        A[f"B{r}"] = val; A[f"B{r}"].font = blue; A[f"B{r}"].number_format = fmt
        A[f"C{r}"] = src; A[f"C{r}"].font = note
        ref[label] = f"Assumptions!$B${r}"
    r += 1
for lbl in ["Plug price, low ($/plug)", "Plug price, high ($/plug)", "Plugs per sq ft (15–18 in. spacing)"]:
    A[ref[lbl].split("!")[1].replace("$", "")].fill = yellow
A.column_dimensions["A"].width = 52; A.column_dimensions["B"].width = 12; A.column_dimensions["C"].width = 80
R = lambda k: ref[k]

# ---------------- Budget ----------------
B = wb.create_sheet("Budget", 0)
B["A1"] = "Front yard — line-item budget"; B["A1"].font = title
B["A2"] = "Hypothetical plan. Quantities pull from Assumptions (green). Edit blue cells there; totals update."; B["A2"].font = note
heads = ["Phase", "When", "Item", "Qty", "Unit", "Unit $ low", "Unit $ high", "Total low", "Total high", "Optional?", "Source / note"]
for i, h in enumerate(heads, 1):
    c = B.cell(row=4, column=i, value=h); c.font = hdr; c.fill = hfill; c.alignment = Alignment(wrap_text=True)
plug_q = lambda area: f"=ROUND({R(area)}*{R('Plugs per sq ft (15–18 in. spacing)')},0)"
mulch_q = lambda area: f"=ROUND({R(area)}*{R('Smother mulch depth (in.)')}/12/27,1)"
PL, PH = R("Plug price, low ($/plug)"), R("Plug price, high ($/plug)")
SL, SH = R("Native shrub, low ($/each)"), R("Native shrub, high ($/each)")
ML, MH = R("Free mulch/topsoil donation, low ($/cu yd)"), R("Free mulch/topsoil donation, high ($/cu yd)")
items = [
 ("1", "Fall 2026", "Cardboard for smothering", 1, "lot", 0, 0, "N", "Free: appliance, bike and furniture store boxes"),
 ("1", "Fall 2026", "Mulch over cardboard", mulch_q("Phase 1: new area to smother"), "cu yd", "="+ML, "="+MH, "N", "City giveaway (donation)"),
 ("1", "Spring 2027", "Prairie plugs, corner bed", plug_q("Phase 1: corner bed to plant (new 165 + gaps in existing)"), "plugs", "="+PL, "="+PH, "N", "Buy after L2L award notice to keep it reimbursable"),
 ("1", "Spring 2027", "Low natives around stump island", plug_q("Phase 1: stump island bed (Z3 expanded around T1 stump)"), "plugs", "="+PL, "="+PH, "N", "Now full afternoon sun since T1 came down"),
 ("1", "Spring 2027", "Shallow dish for bee bath on stump", 1, "each", 0, 20, "Y", "Estimate; a saucer with pebbles works"),
 ("1", "Spring 2027", "Native shrubs, foundation bed", 2, "each", "="+SL, "="+SH, "N", "Estimate, unverified"),
 ("1", "Fall 2026", "Soil test", 1, "test", 20, 30, "Y", "Estimate, unverified: UMN Soil Testing Lab"),
 ("1", "Spring 2027", "Gopher State One Call (811) locate", 1, "call", 0, 0, "N", "Free; required before digging"),
 ("2", "Jun 2027", "Mulch over cardboard, Z4 + south border", mulch_q("Phase 2: area to smother (Z4 + south border)"), "cu yd", "="+ML, "="+MH, "N", "City giveaway (donation)"),
 ("2", "Aug 2027", "Bee lawn seed, boulevard (Option A)", f"=ROUND({R('Boulevard bee lawn area (Option A)')}/1000*{R('Bee lawn seeding rate (lb per 1,000 sq ft)')},1)", "lb", "="+R("Bee lawn seed, low ($/lb)"), "="+R("Bee lawn seed, high ($/lb)"), "N", "UMN bee lawn mix"),
 ("2", "Aug 2027", "Core aerator rental", 1, "rental", "="+R("Core aerator rental, low ($)"), "="+R("Core aerator rental, high ($)"), "Y", "Only if the boulevard turf is compacted; hand tools are fine for ~265 sq ft"),
 ("1", "Feb–Mar 2027", "Frost-seed touch-up: white clover, self-heal, thyme", 1, "lot", 15, 40, "N", "Estimate, unverified. BWSR DIY rates per 1,000 sq ft: ~3 oz clover, ~4 oz self-heal, ~1 oz thyme"),
 ("1", "Fall 2026", "Crocus bulbs in the lawn for early-spring forage", 100, "bulbs", 0.25, 0.45, "Y", "Estimate, unverified. Non-native but well-behaved; plant before the ground freezes"),
 ("1", "Spring 2027", "Native violets / wild strawberry plugs for the lawn", 38, "plugs", "="+PL, "="+PH, "Y", "One tray tucked into thin spots; early bloomers that tolerate mowing"),
 ("2", "Aug 2027", "Compost / topsoil topdressing", 1, "cu yd", "="+ML, "="+MH, "N", "City topsoil or Olmsted County compost site"),
 ("2", "Sep 2027", "Woodland plugs, shade bed (Z4)", plug_q("Phase 2: shade bed area for plugs (after shrubs)"), "plugs", "="+PL, "="+PH, "N", "Pennsylvania sedge, wild geranium, zigzag goldenrod, etc."),
 ("2", "Sep 2027", "Native shrubs, shade bed", 3, "each", "="+SL, "="+SH, "N", "Estimate, unverified"),
 ("1", "Spring 2027", "Rain barrel at front downspout", 1, "each", "="+R("Rain barrel, low ($)"), "="+R("Rain barrel, high ($)"), "Y", "City cost-share (90% up to $100) only in Cascade Creek pilot neighborhoods so far"),
 ("1", "Spring 2027", "Downspout diverter + overflow hose to bed", 1, "kit", "="+R("Diverter + overflow hose, low ($)"), "="+R("Diverter + overflow hose, high ($)"), "Y", "Route overflow 10+ ft from the foundation"),
 ("3", "Spring 2028", "Prairie plugs, south border", plug_q("Phase 3: south border bed"), "plugs", "="+PL, "="+PH, "N", "Seed instead (~$50 per 500 sq ft) to save ~$250, but slower and weedier"),
 ("3", "Fall 2027", "Mulch over cardboard, boulevard (Option B)", mulch_q("Phase 3: boulevard core (Option B)"), "cu yd", "="+ML, "="+MH, "Y", "Only if Option B"),
 ("3", "Spring 2028", "Short native plugs, boulevard (Option B)", plug_q("Phase 3: boulevard core (Option B)"), "plugs", "="+PL, "="+PH, "Y", "Needs a free Natural Landscape Permit"),
 ("3", "Winter 2027–28", "Natural Landscape Permit (boulevard)", 1, "permit", 0, 0, "Y", "Free"),
 ("3", "Spring 2028", "Replacement plugs (losses)", None, "plugs", "="+PL, "="+PH, "N", "Allowance, % of plugs above"),
]
r0 = 5; r = r0
plug_rows = []
for ph, when, item, q, unit, lo, hi, opt, src in items:
    B[f"A{r}"], B[f"B{r}"], B[f"C{r}"], B[f"E{r}"], B[f"J{r}"], B[f"K{r}"] = ph, when, item, unit, opt, src
    if unit == "plugs" and q is not None and opt == "N": plug_rows.append(r)
    if q is None:
        q = f"=ROUND(({'+'.join('D'+str(x) for x in plug_rows)})*{R('Replacement allowance (% of plugs)')},0)"
    B[f"D{r}"] = q; B[f"F{r}"] = lo; B[f"G{r}"] = hi
    B[f"H{r}"] = f"=D{r}*F{r}"; B[f"I{r}"] = f"=D{r}*G{r}"
    for col, v in (("D", q), ("F", lo), ("G", hi)):
        B[f"{col}{r}"].font = green if isinstance(v, str) and "Assumptions" in v else (black if isinstance(v, str) else blue)
    B[f"D{r}"].number_format = '#,##0.0'
    for col in "FG": B[f"{col}{r}"].number_format = USD2
    for col in "HI": B[f"{col}{r}"].number_format = USD
    for col in "ABCEJ": B[f"{col}{r}"].font = black
    B[f"K{r}"].font = note
    r += 1
last = r - 1
B[f"C{r}"] = "Total, all lines"; B[f"C{r}"].font = bold
B[f"H{r}"] = f"=SUM(H{r0}:H{last})"; B[f"I{r}"] = f"=SUM(I{r0}:I{last})"
for col in "HI": B[f"{col}{r}"].number_format = USD; B[f"{col}{r}"].font = bold; B[f"{col}{r}"].border = top
widths = [7, 14, 40, 8, 8, 10, 10, 11, 11, 9, 60]
for i, w in enumerate(widths, 1): B.column_dimensions[get_column_letter(i)].width = w
B.freeze_panes = "A5"

# ---------------- Summary ----------------
S = wb.create_sheet("Summary", 0)
S["A1"] = "Budget summary by phase"; S["A1"].font = title
S["A2"] = "Required = base plan with boulevard Option A (bee lawn). Optional = soil test, rain barrel kit, boulevard Option B."; S["A2"].font = note
for i, h in enumerate(["Phase", "Timing", "Required low", "Required high", "Optional low", "Optional high"], 1):
    c = S.cell(row=4, column=i, value=h); c.font = hdr; c.fill = hfill
phases = [("1", "Fall 2026 – spring 2027"), ("2", "Summer – fall 2027"), ("3", "Fall 2027 – spring 2028")]
rng = lambda col: f"Budget!${col}${r0}:${col}${last}"
for i, (ph, when) in enumerate(phases):
    rr = 5 + i
    S[f"A{rr}"] = ph; S[f"B{rr}"] = when
    S[f"C{rr}"] = f'=SUMIFS({rng("H")},{rng("A")},A{rr},{rng("J")},"N")'
    S[f"D{rr}"] = f'=SUMIFS({rng("I")},{rng("A")},A{rr},{rng("J")},"N")'
    S[f"E{rr}"] = f'=SUMIFS({rng("H")},{rng("A")},A{rr},{rng("J")},"Y")'
    S[f"F{rr}"] = f'=SUMIFS({rng("I")},{rng("A")},A{rr},{rng("J")},"Y")'
    for col in "CDEF": S[f"{col}{rr}"].font = green; S[f"{col}{rr}"].number_format = USD
S["B8"] = "Total"; S["B8"].font = bold
for col in "CDEF":
    S[f"{col}8"] = f"=SUM({col}5:{col}7)"; S[f"{col}8"].font = bold; S[f"{col}8"].number_format = USD; S[f"{col}8"].border = top
S["B9"] = "Less Lawns to Legumes (if awarded)"
S["C9"] = f"=-{R('Lawns to Legumes reimbursement (if awarded)')}"; S["D9"] = "=C9"
S["B10"] = "Less Rochester Garden Grant (if awarded)"
S["C10"] = f"=-{R('Rochester Garden Grant (if awarded)')}"; S["D10"] = "=C10"
S["B11"] = "Net cash, required plan"; S["B11"].font = bold
S["C11"] = "=MAX(0,C8+C9+C10)"; S["D11"] = "=MAX(0,D8+D9+D10)"
for c in ("C9", "D9", "C10", "D10", "C11", "D11"): S[c].number_format = USD
S["C9"].font = green; S["D9"].font = black; S["C10"].font = green; S["D10"].font = black
for c in ("C11", "D11"): S[c].font = bold
S["B13"] = "Plugs needed (required plan)"; S["C13"] = f'=SUMIFS({rng("D")},{rng("E")},"plugs",{rng("J")},"N")'; S["C13"].number_format = '#,##0'; S["C13"].font = green
S["B14"] = "Mulch needed, all smothering (cu yd)"; S["C14"] = f'=SUMIFS({rng("D")},{rng("E")},"cu yd")'; S["C14"].number_format = '0.0'; S["C14"].font = green
for i, w in enumerate([8, 36, 14, 14, 14, 14], 1): S.column_dimensions[get_column_letter(i)].width = w

# ---------------- Sources ----------------
X = wb.create_sheet("Sources")
X["A1"] = "Price and program sources (opened Nov 6, 2026)"; X["A1"].font = title
src = [
 ("Lawns to Legumes: Spring 2027 applications open, due Nov 30, 2026, up to $400", "https://bluethumb.org/lawns-to-legumes/apply/"),
 ("Olmsted SWCD 2026 plant & seed sale (plug kits $80/36; bee lawn $90/1,000 sq ft)", "https://www.olmstedcounty.gov/sites/default/files/2025-12/2026%20Plant%20%20Seed%20descriptions_508Compliant.pdf"),
 ("New Leaf Natives 38-plug single-species trays ($75–$115)", "https://newleafnatives.com/collections/single-species-trays?page=1"),
 ("Nokomis East bee lawn seed, $17.50/lb, 5 lb per 1,000 sq ft", "https://www.nokomiseast.org/product-page/bee-lawn-seed"),
 ("Mann Lake bee lawn seed mix, $29.99–$109.99", "https://www.mannlakeltd.com/seeding-forage/bee-lawn-pollinator-friendly-seed-mix"),
 ("Home Depot aerator rental (~$81 per 4 hr, $116 per day)", "https://www.housedigest.com/2253877/dont-waste-money-pricey-lawn-aerators-rent-from-home-depot/"),
 ("Olmsted County compost site (suggested $20 per pickup load)", "https://www.olmstedcounty.gov/residents/garbage-recycling/compost-site/compost-site-self-serve-compost"),
 ("Rochester Garden Grants (up to $1,000; apply Oct 1–Dec 31)", "https://www.rochestermn.gov/home-property-utilities/sustainability-environment/garden-grants/"),
 ("Rochester Rain Barrel Program (90% up to $100, Cascade Creek pilot areas)", "https://rochestermn.qscend.com/311/knowledgebase/article/21997"),
 ("Livingston Co. MI 2026 rain barrel sale ($69.95), price reference only", "https://www.whmi.com/news/article/49654"),
 ("City topsoil and mulch giveaway", "Free with a requested donation; confirm location and hours"),
]
for i, (a, b) in enumerate(src, 3):
    X[f"A{i}"] = a; X[f"B{i}"] = b; X[f"A{i}"].font = black; X[f"B{i}"].font = Font(name=F, color="0563C1", underline="single") if b.startswith("http") else black
    if b.startswith("http"): X[f"B{i}"].hyperlink = b
X.column_dimensions["A"].width = 80; X.column_dimensions["B"].width = 70

# Keep workbook metadata anonymous
wb.properties.creator = None
wb.properties.lastModifiedBy = None

wb.save("Front_Yard_Budget.xlsx")
print("Wrote Front_Yard_Budget.xlsx (budget rows", r0, "to", last, ")")
