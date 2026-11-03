"""
luminograph.py — ID Sign-Wave generator for Project Duality.

Takes a subject's base stats (16 desires, mass, Returnite units, max capacity,
control, ID number) and produces:
  * Luminans threshold, capacity %, stage
  * the 8 desire categories and their I/A/E vector sum
  * Evocation status and outcome (Lumenborn / Stellaborn / Desir)
  * the Identifying Signature Wavelength (ID Sign-Wave) as a sum of sine
    waves: composite (A), radial print (D) and component stack (C)

The core uses only the Python standard library, so the same file runs
locally and in the browser (via Pyodide on GitHub Pages).
Plotting (matplotlib) is only used when run from the command line.

Usage:
    python luminograph.py --example > subject.json
    python luminograph.py subject.json                  # overview.png + stack.png
    python luminograph.py subject.json --transparent    # + transparent A and D PNGs
    python luminograph.py subject.json --json
"""

import json
import math
import random

# ---------------------------------------------------------------------------
# Editable constants
# ---------------------------------------------------------------------------

BODY_DENSITY_KG_PER_L = 1.01      # average human body density
RETURNITE_PER_5MM3 = 1e-5         # 1 Luminans = 1e-5 units in 5 mm^3
MM3_PER_L = 1_000_000

# Stage boundaries (capacity %)
VERATIA_MIN = 5
VITIA_MIN = 10
RECKONING_MIN = 26

# A category "peaks" when the average of its two desires is above this.
PEAK_THRESHOLD = 80

# Control placeholder formula (to be discussed):
#   required control = BASE + CHAOS_WEIGHT * chaos + PER_EXTRA_PEAK * (peaks - 1)
CONTROL_BASE = 30
CONTROL_CHAOS_WEIGHT = 50
CONTROL_PER_EXTRA_PEAK = 5

# Pre-awakening drift: each desire wanders around its entered value by up to
# this many points. Peaks and the Evocation trigger use the entered values.
DRIFT_AMPLITUDE = 10

# If the resultant is shorter than this fraction of the total magnitude,
# the subject reads as sitting at the centre of the chart.
CENTRE_FRACTION = 0.05

# ---------------------------------------------------------------------------
# Desires and categories
# ---------------------------------------------------------------------------

DESIRES = [
    "Power", "Status",
    "Independence", "Honor",
    "Eating", "Physical Exercise",
    "Family", "Social Contact",
    "Tranquility", "Acceptance",
    "Romance", "Idealism",
    "Vengeance", "Order",
    "Curiosity", "Saving",
]

# Chart axes:
#   x: Insular (-)  <->  Alteral (+)     [scope]
#   y: Efferent (-) <->  Afferent (+)    [flow]
# Angle in degrees, measured anticlockwise from the Alteral pole.
CATEGORIES = [
    {"name": "Dominion",     "desires": ("Power", "Status"),                 "angle": 0,   "direction": "Alteral pole"},
    {"name": "Kinship",      "desires": ("Family", "Social Contact"),        "angle": 45,  "direction": "A-A (Allurate)"},
    {"name": "Serenity",     "desires": ("Tranquility", "Acceptance"),       "angle": 90,  "direction": "Afferent pole"},
    {"name": "Voracity",     "desires": ("Curiosity", "Saving"),             "angle": 135, "direction": "I-A (Materiatic)"},
    {"name": "Corporeality", "desires": ("Eating", "Physical Exercise"),     "angle": 180, "direction": "Insular pole"},
    {"name": "Sovereignty",  "desires": ("Independence", "Honor"),           "angle": 225, "direction": "I-E (Exultate)"},
    {"name": "Hierarchy",    "desires": ("Vengeance", "Order"),              "angle": 270, "direction": "Efferent pole"},
    {"name": "Devotion",     "desires": ("Romance", "Idealism"),             "angle": 315, "direction": "A-E (Karmatic)"},
]

QUADRANTS = {
    ("I", "A"): "Materiatic",
    ("A", "A"): "Allurate",
    ("I", "E"): "Exultate",
    ("A", "E"): "Karmatic",
}

# ---------------------------------------------------------------------------
# ID Sign-Wave layout (relative frequency units, "rf" = cycles per sample period)
# ---------------------------------------------------------------------------

LOW_BAND = (0.0, 30.0)    # field device: dominant peak + category comb
HIGH_BAND = (30.0, 100.0)  # lab equipment: fine lines (ID)
DOMINANT_CENTRE = 8.0      # rf of the dominant peak at neutral flow
DOMINANT_SPAN = 6.0        # afferent shifts down, efferent shifts up
COMB_START, COMB_STEP = 16.0, 1.6
FINE_LINE_COUNT = 32

EXAMPLE_SUBJECT = {
    "id": 4172,
    "name": "Example subject",
    "origin": "Proto-Human",
    "mass_kg": 70,
    "returnite_units": 300,
    "max_capacity_units": 1000,
    "control": 60,
    "drift_t": 0.0,
    "desires": {
        "Power": 35, "Status": 30,
        "Independence": 55, "Honor": 60,
        "Eating": 40, "Physical Exercise": 45,
        "Family": 70, "Social Contact": 65,
        "Tranquility": 50, "Acceptance": 45,
        "Romance": 85, "Idealism": 90,
        "Vengeance": 20, "Order": 35,
        "Curiosity": 75, "Saving": 30,
    },
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _clamp(v, lo, hi):
    return max(lo, min(hi, v))


def _gauss(x, centre, width, amp):
    d = (x - centre) / width
    return amp * math.exp(-0.5 * d * d)


def _clean_subject(subject):
    s = dict(EXAMPLE_SUBJECT)
    s.update(subject or {})
    desires = {}
    raw = s.get("desires") or {}
    for d in DESIRES:
        desires[d] = _clamp(float(raw.get(d, 50)), 1, 100)
    s["desires"] = desires
    s["id"] = int(s.get("id", 0))
    s["mass_kg"] = max(0.001, float(s["mass_kg"]))
    s["returnite_units"] = max(0.0, float(s["returnite_units"]))
    s["max_capacity_units"] = max(0.001, float(s["max_capacity_units"]))
    s["control"] = _clamp(float(s.get("control", 50)), 1, 100)
    s["drift_t"] = float(s.get("drift_t", 0.0))
    if s.get("origin") not in ("Proto-Human", "Neo-Human"):
        s["origin"] = "Proto-Human"
    return s


# ---------------------------------------------------------------------------
# Core calculations
# ---------------------------------------------------------------------------

def luminans_threshold(mass_kg):
    """Returnite units needed to reach 1 Luminans per 5 mm^3 across the body."""
    volume_l = mass_kg / BODY_DENSITY_KG_PER_L
    units = volume_l * MM3_PER_L / 5 * RETURNITE_PER_5MM3
    return volume_l, units


def stage_for(capacity_pct):
    if capacity_pct >= RECKONING_MIN:
        return "The Reckoning"
    if capacity_pct >= VITIA_MIN:
        return "The Vitia"
    if capacity_pct >= VERATIA_MIN:
        return "The Veratia"
    return "Normal"


def category_values(desires):
    out = []
    for c in CATEGORIES:
        a, b = c["desires"]
        avg = (desires[a] + desires[b]) / 2
        rad = math.radians(c["angle"])
        out.append({
            "name": c["name"],
            "desires": list(c["desires"]),
            "direction": c["direction"],
            "angle": c["angle"],
            "value": avg,
            "x": avg * math.cos(rad),
            "y": avg * math.sin(rad),
            "peak": avg > PEAK_THRESHOLD,
        })
    return out


def quadrant_for(x, y, near_centre):
    if near_centre:
        return "Centre", "-"
    scope = "A" if x >= 0 else "I"
    flow = "A" if y >= 0 else "E"
    return QUADRANTS[(scope, flow)], f"{scope}-{flow}"


def drift_desires(desires, seed, t):
    """Pre-awakening drift: desires wander around their entered values."""
    rng = random.Random(seed * 31 + 5)
    out = {}
    for d in DESIRES:
        speed = 0.5 + 0.7 * rng.random()
        phase = rng.random() * math.tau
        out[d] = _clamp(desires[d] + DRIFT_AMPLITUDE * math.sin(t * speed + phase), 1, 100)
    return out


def _vector(cats):
    rx = sum(c["x"] for c in cats)
    ry = sum(c["y"] for c in cats)
    total = sum(c["value"] for c in cats)
    magnitude = math.hypot(rx, ry)
    coherence = magnitude / total if total else 0.0
    near_centre = coherence < CENTRE_FRACTION
    quadrant, code = quadrant_for(rx, ry, near_centre)
    angle = math.degrees(math.atan2(ry, rx)) % 360 if magnitude else 0.0
    return rx, ry, total, magnitude, coherence, quadrant, code, angle


def analyse(subject):
    """Main entry point. Returns a dict with every derived value and the wave components."""
    s = _clean_subject(subject)
    notes = []

    volume_l, threshold = luminans_threshold(s["mass_kg"])
    units = s["returnite_units"]
    capacity_pct = units / s["max_capacity_units"] * 100
    luminans_ratio = units / threshold
    past_threshold = luminans_ratio >= 1
    stage = stage_for(capacity_pct)

    cats = category_values(s["desires"])
    peaks = [c["name"] for c in cats if c["peak"]]
    rx, ry, total, magnitude, coherence, quadrant, code, angle = _vector(cats)

    # Chaos: how much the *stronger-than-average* desires pull in different
    # directions. One dominant pull = calm; several opposing pulls = chaotic.
    mean = total / len(cats)
    wx = wy = wsum = 0.0
    for c in cats:
        w = max(0.0, c["value"] - mean)
        rad = math.radians(c["angle"])
        wx += w * math.cos(rad)
        wy += w * math.sin(rad)
        wsum += w
    chaos = 1 - (math.hypot(wx, wy) / wsum) if wsum else 0.0

    # Evocation: past the Luminans threshold, and either Reckoning,
    # or Vitia with at least one peaking category.
    in_evocation = past_threshold and (
        capacity_pct >= RECKONING_MIN
        or (capacity_pct >= VITIA_MIN and len(peaks) >= 1)
    )

    required = _clamp(
        CONTROL_BASE
        + CONTROL_CHAOS_WEIGHT * chaos
        + CONTROL_PER_EXTRA_PEAK * max(0, len(peaks) - 1),
        0, 100,
    )
    margin = s["control"] - required

    if in_evocation:
        if margin >= 0:
            outcome = "Lumenborn" if s["origin"] == "Proto-Human" else "Stellaborn"
        else:
            outcome = "Desir"
        awakened = True
        instability = _clamp(-margin / 50, 0, 1)
    else:
        outcome = None
        awakened = False
        instability = _clamp(0.3 + 0.5 * chaos, 0, 1)

    # Pre-awakening drift: the desires wander, moving the I/A/E position and
    # the low-band waves. Peaks and the Evocation trigger use entered values.
    # The ID fine lines never drift.
    drifted = None
    if past_threshold and not awakened and s["drift_t"]:
        drifted = drift_desires(s["desires"], s["id"], s["drift_t"])
        base_peak = {c["name"]: c["peak"] for c in cats}
        cats = category_values(drifted)
        for c in cats:
            c["peak"] = base_peak[c["name"]]
        rx, ry, total, magnitude, coherence, quadrant, code, angle = _vector(cats)

    if not past_threshold:
        notes.append("Below Luminans threshold: no ID Sign-Wave is emitted.")
        if stage in ("The Vitia", "The Reckoning"):
            notes.append("In this stage but below threshold: this subject cannot undergo the Evocation.")
    elif not in_evocation:
        notes.append("Pre-awakening: desires drift, shifting the I/A/E position and the Sign-Wave. The ID fine lines stay fixed.")
    if outcome == "Desir":
        notes.append("Desir assumed to keep a permanent ID Sign-Wave (unconfirmed).")
    notes.append("Control formula is a placeholder.")


    comps = components(s, cats, rx, ry, total, luminans_ratio,
                       past_threshold, awakened, instability)

    return {
        "subject": s,
        "volume_l": volume_l,
        "luminans_threshold_units": threshold,
        "luminans_ratio": luminans_ratio,
        "past_threshold": past_threshold,
        "capacity_pct": capacity_pct,
        "stage": stage,
        "categories": cats,
        "peaks": peaks,
        "resultant": {"x": rx, "y": ry, "magnitude": magnitude, "angle": angle},
        "total_magnitude": total,
        "coherence": coherence,
        "chaos": chaos,
        "quadrant": quadrant,
        "quadrant_code": code,
        "in_evocation": in_evocation,
        "required_control": required,
        "control_margin": margin,
        "outcome": outcome,
        "awakened": awakened,
        "instability": instability,
        "drifted_desires": drifted,
        "components": comps,
        "notes": notes,
    }


# ---------------------------------------------------------------------------
# ID Sign-Wave components
#
# The Sign-Wave is a sum of sine waves. Each component has a frequency (rf),
# an amplitude and a starting phase:
#   dominant  - low band; flow sets frequency, scope sets single/doublet
#   category  - low band; one per category, amplitude = category value,
#               phase = the category's I/A/E direction angle
#   fine      - high band; positions and phases seeded by the ID number,
#               identical from first emission to the permanent wave
#   noise     - instability; rough high-frequency texture, stronger when
#               the subject is unstable
# ---------------------------------------------------------------------------

NOISE_COUNT = 24
NOISE_BAND = (100.0, 260.0)


def components(s, cats, rx, ry, total, ratio, past_threshold, awakened, instability):
    comps = []
    if not past_threshold:
        return comps

    amp = 0.4 + 0.6 * _clamp(math.log10(ratio), 0, 1)

    # Dominant (flow -> frequency, scope -> shape)
    nx = rx / total if total else 0.0   # + Alteral / - Insular
    ny = ry / total if total else 0.0   # + Afferent / - Efferent
    f0 = DOMINANT_CENTRE - DOMINANT_SPAN * _clamp(ny * 2, -1, 1)
    if nx > 0:  # Alteral: doublet
        split = 3.0 * _clamp(nx * 2, 0, 1)
        comps.append({"kind": "dominant", "label": "Dominant", "rf": f0 - split / 2, "amp": amp * 0.6, "phase": 0.0})
        comps.append({"kind": "dominant", "label": "Dominant", "rf": f0 + split / 2, "amp": amp * 0.6, "phase": math.pi / 2})
    else:       # Insular: single
        comps.append({"kind": "dominant", "label": "Dominant", "rf": f0, "amp": amp, "phase": 0.0})

    # Categories
    for i, c in enumerate(cats):
        comps.append({"kind": "category", "label": c["name"], "peak": c["peak"],
                      "rf": COMB_START + i * COMB_STEP,
                      "amp": amp * 0.5 * c["value"] / 100,
                      "phase": math.radians(c["angle"])})

    # Fine lines (ID): fixed by the ID number from first emission onward.
    rng = random.Random(s["id"])
    rng_phase = random.Random(s["id"] * 7919 + 1)
    for _ in range(FINE_LINE_COUNT):
        pos = HIGH_BAND[0] + 2 + (HIGH_BAND[1] - HIGH_BAND[0] - 4) * rng.random()
        a = 0.25 + 0.75 * rng.random()
        comps.append({"kind": "fine", "label": "Fine lines (ID)",
                      "rf": pos, "amp": amp * 0.6 * a,
                      "phase": rng_phase.random() * math.tau})

    # Instability noise
    if instability > 0:
        rng_n = random.Random(s["id"] * 104729 + 2)
        for _ in range(NOISE_COUNT):
            comps.append({"kind": "noise", "label": "Instability",
                          "rf": NOISE_BAND[0] + (NOISE_BAND[1] - NOISE_BAND[0]) * rng_n.random(),
                          "amp": amp * 0.12 * instability * (0.5 + 0.5 * rng_n.random()),
                          "phase": rng_n.random() * math.tau})
    return comps


def _sum(comps, ts, kinds=None, integer_freq=False):
    out = []
    use = [c for c in comps if kinds is None or c["kind"] in kinds]
    for t in ts:
        v = 0.0
        for c in use:
            f = round(c["rf"]) if integer_freq else c["rf"]
            v += c["amp"] * math.sin(math.tau * f * t + c["phase"])
        out.append(v)
    return out


def composite(result, n=2400, t1=1.0):
    """A · Composite Sign-Wave: every component summed over one sample period."""
    ts = [t1 * i / (n - 1) for i in range(n)]
    return ts, _sum(result["components"], ts)


def radial(result, n=2400):
    """D · Radial print: one period wrapped into a circle.
    Frequencies are rounded to whole cycles so the loop closes cleanly."""
    ts = [i / n for i in range(n)]
    return ts, _sum(result["components"], ts, integer_freq=True)


def stack(result, n=1500, t1=0.5):
    """C · Component stack: each part of the signal on its own row."""
    ts = [t1 * i / (n - 1) for i in range(n)]
    comps = result["components"]
    rows = []
    dom = [c for c in comps if c["kind"] == "dominant"]
    if dom:
        rows.append({"label": "Dominant", "kind": "dominant", "peak": False, "y": _sum(dom, ts)})
    for c in comps:
        if c["kind"] == "category":
            rows.append({"label": c["label"], "kind": "category", "peak": c["peak"], "y": _sum([c], ts)})
    fine = [c for c in comps if c["kind"] == "fine"]
    if fine:
        rows.append({"label": "Fine lines (ID)", "kind": "fine", "peak": False, "y": _sum(fine, ts)})
    noise = [c for c in comps if c["kind"] == "noise"]
    if noise:
        rows.append({"label": "Instability", "kind": "noise", "peak": False, "y": _sum(noise, ts)})
    return ts, rows


def _r(vals):
    return [round(v, 4) for v in vals]


def analyse_json(subject_json, with_stack=True):
    """JSON in, JSON out (used by the web page). Includes the A, D and C waves."""
    r = analyse(json.loads(subject_json))
    _, a = composite(r)
    _, d = radial(r)
    r["waves"] = {"composite": _r(a), "radial": _r(d)}
    if with_stack:
        _, rows = stack(r)
        r["waves"]["stack"] = [dict(row, y=_r(row["y"])) for row in rows]
    return json.dumps(r)


# ---------------------------------------------------------------------------
# Command line
# ---------------------------------------------------------------------------

def summary_text(r):
    s = r["subject"]
    lines = [
        f"ID {s['id']}  {s.get('name', '')}  ({s['origin']})",
        f"Mass {s['mass_kg']:.1f} kg  ->  volume {r['volume_l']:.1f} L",
        f"Luminans threshold {r['luminans_threshold_units']:.1f} units",
        f"Returnite {s['returnite_units']:.1f} / {s['max_capacity_units']:.1f} units  "
        f"({r['capacity_pct']:.1f}%)",
        f"Stage: {r['stage']}",
        f"I/A/E: {r['quadrant']} ({r['quadrant_code']})  "
        f"magnitude {r['resultant']['magnitude']:.1f}  angle {r['resultant']['angle']:.0f} deg",
        f"Peaks: {', '.join(r['peaks']) or 'none'}",
        f"Chaos {r['chaos']:.2f}  required control {r['required_control']:.0f}  "
        f"control {s['control']:.0f}",
        f"Evocation: {'yes' if r['in_evocation'] else 'no'}  "
        f"Outcome: {r['outcome'] or '-'}",
    ]
    return "\n".join(lines + ["", *r["notes"]])


BG, PANEL, GRID, TXT, MUT = "#0b0f14", "#11171f", "#232c38", "#e3e9f0", "#8593a3"
WAVE, HIGHC, PEAKC, OKC, NOISEC, RESC = "#7ee8fa", "#b48cff", "#f0883e", "#3fb950", "#f85149", "#f778ba"


def _style(ax, title=None):
    ax.set_facecolor(PANEL)
    for sp in ax.spines.values():
        sp.set_color(GRID)
    ax.tick_params(colors=MUT)
    if title:
        ax.set_title(title, color=TXT, loc="left")


def _radial_xy(vals, inner=1.0, depth=0.35):
    m = max(1e-9, max(abs(v) for v in vals))
    xs, ys = [], []
    for i, v in enumerate(vals + vals[:1]):
        th = math.tau * i / len(vals)
        rr = inner + depth * v / m
        xs.append(rr * math.cos(th))
        ys.append(rr * math.sin(th))
    return xs, ys


def plot_overview(r, out_path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig = plt.figure(figsize=(14, 9), facecolor=BG)
    gs = fig.add_gridspec(2, 3, height_ratios=[0.8, 1.2])
    ax_a = fig.add_subplot(gs[0, :])
    ax_d = fig.add_subplot(gs[1, 0])
    ax_c = fig.add_subplot(gs[1, 1])
    ax_t = fig.add_subplot(gs[1, 2])

    _style(ax_a, "A · Composite Sign-Wave")
    if r["components"]:
        ts, ys = composite(r)
        ax_a.plot(ts, ys, color=WAVE, lw=0.8)
        ax_a.fill_between(ts, ys, color=WAVE, alpha=0.08)
    else:
        ax_a.text(0.5, 0, "Below Luminans threshold — no ID Sign-Wave", color=NOISEC, ha="center")
    ax_a.axhline(0, color=MUT, lw=0.6)
    ax_a.set_xlim(0, 1)
    ax_a.set_xlabel("time (one sample period)", color=MUT)
    ax_a.set_ylabel("amplitude", color=MUT)

    _style(ax_d, "D · Radial print")
    ax_d.set_aspect("equal")
    ax_d.set_xticks([])
    ax_d.set_yticks([])
    if r["components"]:
        _, vals = radial(r)
        xs, ys = _radial_xy(vals)
        ax_d.plot(xs, ys, color=WAVE, lw=0.8)
        ax_d.fill(xs, ys, color=WAVE, alpha=0.08)
    ax_d.set_xlim(-1.45, 1.45)
    ax_d.set_ylim(-1.45, 1.45)

    _style(ax_c, "I/A/E chart")
    cats = r["categories"]
    R = r["resultant"]
    lim = max(135, R["magnitude"] * 1.12)
    ax_c.set_xlim(-lim, lim)
    ax_c.set_ylim(-lim, lim)
    ax_c.set_aspect("equal")
    ax_c.set_xticks([])
    ax_c.set_yticks([])

    def pt(rad, deg):
        return rad * math.cos(math.radians(deg)), rad * math.sin(math.radians(deg))

    def ring(rad):
        p = [pt(rad, c["angle"]) for c in cats]
        return [x for x, _ in p] + [p[0][0]], [y for _, y in p] + [p[0][1]]

    for rad in (25, 50, 75, 100):
        ax_c.plot(*ring(rad), color=GRID, lw=0.8)
    for c in cats:
        x, y = pt(100, c["angle"])
        ax_c.plot([0, x], [0, y], color=GRID, lw=0.8)
    ax_c.plot(*ring(80), color=PEAKC, lw=0.8, ls="--", alpha=0.45)
    vals = [pt(c["value"], c["angle"]) for c in cats]
    xs = [x for x, _ in vals] + [vals[0][0]]
    ys = [y for _, y in vals] + [vals[0][1]]
    ax_c.fill(xs, ys, color=OKC, alpha=0.15)
    ax_c.plot(xs, ys, color=OKC, lw=1.4)
    poles = {90: "AFFERENT", 270: "EFFERENT", 180: "INSULAR", 0: "ALTERAL",
             135: "MATERIATIC · I-A", 45: "ALLURATE · A-A", 225: "EXULTATE · I-E", 315: "KARMATIC · A-E"}
    for c, (x, y) in zip(cats, vals):
        col = PEAKC if c["peak"] else OKC
        ax_c.plot(x, y, "o", color=col, ms=6 if c["peak"] else 4)
        lx, ly = pt(114, c["angle"])
        ax_c.text(lx, ly, c["name"], color=PEAKC if c["peak"] else TXT, fontsize=7.5, ha="center", va="center")
        if c["angle"] in poles:
            ax_c.text(lx, ly - 9, poles[c["angle"]], color=MUT, fontsize=6, ha="center", va="center")
    if R["magnitude"] > 0.5:
        ax_c.annotate("", xy=(R["x"], R["y"]), xytext=(0, 0),
                      arrowprops=dict(arrowstyle="-|>,head_length=0.8,head_width=0.45", color=RESC, lw=2.5))
    ax_c.plot(0, 0, "o", color=RESC, ms=4)

    ax_t.axis("off")
    ax_t.text(0, 1, summary_text(r), color=TXT, va="top", family="monospace", fontsize=8)

    fig.tight_layout()
    fig.savefig(out_path, dpi=130, facecolor=BG)
    plt.close(fig)


def plot_stack(r, out_path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    ts, rows = stack(r)
    fig, ax = plt.subplots(figsize=(12, max(3, 0.65 * len(rows) + 1.5)), facecolor=BG)
    _style(ax, "C · Component stack (developer view)")
    colours = {"dominant": WAVE, "fine": HIGHC, "noise": NOISEC}
    for i, row in enumerate(rows):
        off = -i * 1.1
        ys = row["y"]
        scale = 1.0
        if row["kind"] in ("fine", "noise"):
            scale = 0.45 / max(1e-9, max(abs(v) for v in ys))
        col = PEAKC if row["peak"] else colours.get(row["kind"], OKC)
        ax.plot(ts, [off + v * scale for v in ys], color=col, lw=0.9)
        ax.text(-0.005, off, row["label"], ha="right", va="center", fontsize=9, color=col)
    ax.set_yticks([])
    ax.set_xlim(0, ts[-1])
    ax.set_xlabel("time", color=MUT)
    if not rows:
        ax.text(0.25, 0, "Below Luminans threshold — no components", color=NOISEC, ha="center")
    fig.tight_layout()
    fig.savefig(out_path, dpi=120, facecolor=BG)
    plt.close(fig)


def export_transparent(r, composite_path, radial_path, colour=WAVE):
    """Game-ready PNGs of A and D: wave only, transparent background."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    if not r["components"]:
        return False
    ts, ys = composite(r, n=4000)
    fig = plt.figure(figsize=(16, 4), dpi=128)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis("off")
    ax.plot(ts, ys, color=colour, lw=1.4)
    m = max(abs(v) for v in ys) * 1.08
    ax.set_xlim(0, 1)
    ax.set_ylim(-m, m)
    fig.savefig(composite_path, transparent=True)
    plt.close(fig)

    _, vals = radial(r, n=4000)
    xs, yy = _radial_xy(vals)
    fig = plt.figure(figsize=(8, 8), dpi=128)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis("off")
    ax.set_aspect("equal")
    ax.plot(xs, yy, color=colour, lw=1.4)
    ax.set_xlim(-1.4, 1.4)
    ax.set_ylim(-1.4, 1.4)
    fig.savefig(radial_path, transparent=True)
    plt.close(fig)
    return True


def main(argv=None):
    import argparse
    import os
    p = argparse.ArgumentParser(description="ID Sign-Wave generator")
    p.add_argument("subject", nargs="?", help="subject JSON file")
    p.add_argument("--out", default="overview.png", help="overview image (A, D, I/A/E chart, reading)")
    p.add_argument("--stack", default="stack.png", help="component stack image (C, developer view)")
    p.add_argument("--transparent", action="store_true",
                   help="also save transparent PNGs of A and D next to --out")
    p.add_argument("--colour", default=WAVE, help="wave colour for transparent PNGs, e.g. #ffffff")
    p.add_argument("--json", action="store_true", help="print full result as JSON")
    p.add_argument("--example", action="store_true", help="print an example subject")
    a = p.parse_args(argv)

    if a.example:
        print(json.dumps(EXAMPLE_SUBJECT, indent=2))
        return
    subject = EXAMPLE_SUBJECT
    if a.subject:
        with open(a.subject, encoding="utf-8") as f:
            subject = json.load(f)
    r = analyse(subject)
    if a.json:
        print(json.dumps(r, indent=2))
        return
    print(summary_text(r))
    try:
        plot_overview(r, a.out)
        plot_stack(r, a.stack)
        print(f"\nSaved {a.out} and {a.stack}")
        if a.transparent:
            base = os.path.splitext(a.out)[0]
            cp, rp = base + "_composite.png", base + "_radial.png"
            if export_transparent(r, cp, rp, a.colour):
                print(f"Saved {cp} and {rp} (transparent)")
            else:
                print("No transparent PNGs: below Luminans threshold.")
    except ImportError:
        print("\n(matplotlib not installed: pip install matplotlib to save images)")


if __name__ == "__main__":
    main()
