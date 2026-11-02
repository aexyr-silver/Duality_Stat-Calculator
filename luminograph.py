"""
luminograph.py — ID Sign-Wave generator for Project Duality.

Takes a subject's base stats (16 desires, mass, Returnite units, max capacity,
control, ID number) and produces:
  * Luminans threshold, capacity %, stage
  * the 8 desire categories and their I/A/E vector sum
  * Evocation status and outcome (Lumenborn / Stellaborn / Desir)
  * the Identifying Signature Wavelength (ID Sign-Wave) as a spectrum

The core uses only the Python standard library, so the same file runs
locally and in the browser (via Pyodide on GitHub Pages).
Plotting (matplotlib) is only used when run from the command line.

Usage:
    python luminograph.py --example > subject.json
    python luminograph.py subject.json --out signwave.png
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
# ID Sign-Wave layout (relative frequency units, "rf")
# ---------------------------------------------------------------------------

RF_MIN, RF_MAX = 0.0, 100.0
RF_POINTS = 1000
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


def analyse(subject):
    """Main entry point. Returns a dict with every derived value and the spectrum."""
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
    rx = sum(c["x"] for c in cats)
    ry = sum(c["y"] for c in cats)
    total = sum(c["value"] for c in cats)
    magnitude = math.hypot(rx, ry)
    coherence = magnitude / total if total else 0.0
    near_centre = coherence < CENTRE_FRACTION

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
    quadrant, code = quadrant_for(rx, ry, near_centre)
    angle = math.degrees(math.atan2(ry, rx)) % 360 if magnitude else 0.0

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

    if not past_threshold:
        notes.append("Below Luminans threshold: no ID Sign-Wave is emitted.")
        if stage in ("The Vitia", "The Reckoning"):
            notes.append("In this stage but below threshold: this subject cannot undergo the Evocation.")
    elif not in_evocation:
        notes.append("Pre-awakening: the ID Sign-Wave still shifts (drift_t).")
    if outcome == "Desir":
        notes.append("Desir assumed to keep a permanent ID Sign-Wave (unconfirmed).")
    notes.append("Control formula is a placeholder.")

    spectrum = sign_wave(s, cats, rx, ry, total, luminans_ratio,
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
        "spectrum": spectrum,
        "notes": notes,
    }


# ---------------------------------------------------------------------------
# ID Sign-Wave
# ---------------------------------------------------------------------------

def sign_wave(s, cats, rx, ry, total, ratio, past_threshold, awakened, instability):
    step = (RF_MAX - RF_MIN) / (RF_POINTS - 1)
    rf = [RF_MIN + i * step for i in range(RF_POINTS)]
    intensity = [0.0] * RF_POINTS
    lines = []

    if not past_threshold:
        return {"rf": rf, "intensity": intensity, "lines": lines,
                "bands": {"low": LOW_BAND, "high": HIGH_BAND}}

    # Amplitude from how far past threshold the subject is.
    amp = 0.4 + 0.6 * _clamp(math.log10(ratio), 0, 1)
    widen = 1 + 3 * instability

    # --- Low band: dominant peak (flow -> position, scope -> shape) ---
    nx = rx / total if total else 0.0   # + Alteral / - Insular
    ny = ry / total if total else 0.0   # + Afferent / - Efferent
    f0 = DOMINANT_CENTRE - DOMINANT_SPAN * _clamp(ny * 2, -1, 1)
    w0 = 0.7 * widen
    if nx > 0:  # Alteral: peak splits into a doublet
        split = 3.0 * _clamp(nx * 2, 0, 1)
        peaks = [(f0 - split / 2, amp * 0.6), (f0 + split / 2, amp * 0.6)]
    else:       # Insular: single peak, sharper the more insular
        w0 *= 1 - 0.5 * _clamp(-nx * 2, 0, 1)
        peaks = [(f0, amp)]
    for c, a in peaks:
        lines.append({"rf": c, "amp": a, "width": w0, "kind": "dominant"})

    # --- Low band: category comb ---
    for i, c in enumerate(cats):
        a = amp * 0.5 * c["value"] / 100
        lines.append({"rf": COMB_START + i * COMB_STEP, "amp": a,
                      "width": 0.18 * widen, "kind": "category",
                      "label": c["name"], "peak": c["peak"]})

    # --- High band: fine lines seeded by the ID number ---
    rng = random.Random(s["id"])
    t = 0.0 if awakened else s["drift_t"]
    for i in range(FINE_LINE_COUNT):
        pos = HIGH_BAND[0] + 2 + (HIGH_BAND[1] - HIGH_BAND[0] - 4) * rng.random()
        base = 0.25 + 0.75 * rng.random()
        ph1 = rng.random() * math.tau
        ph2 = rng.random() * math.tau
        desire = DESIRES[i % len(DESIRES)]
        a = base * (0.6 + 0.4 * s["desires"][desire] / 100)
        if t:
            pos += 0.8 * math.sin(t * 0.9 + ph1)
            a *= 1 + 0.15 * math.sin(t * 1.3 + ph2)
        lines.append({"rf": pos, "amp": amp * 0.6 * a,
                      "width": 0.12 * widen, "kind": "fine"})

    for ln in lines:
        lo = ln["rf"] - 5 * ln["width"]
        hi = ln["rf"] + 5 * ln["width"]
        i0 = max(0, int((lo - RF_MIN) / step))
        i1 = min(RF_POINTS - 1, int((hi - RF_MIN) / step) + 1)
        for i in range(i0, i1 + 1):
            intensity[i] += _gauss(rf[i], ln["rf"], ln["width"], ln["amp"])

    return {"rf": rf, "intensity": intensity, "lines": lines,
            "bands": {"low": LOW_BAND, "high": HIGH_BAND}}


def analyse_json(subject_json):
    """JSON in, JSON out (used by the web page)."""
    return json.dumps(analyse(json.loads(subject_json)))


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


def plot(r, out_path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig = plt.figure(figsize=(13, 7.5), facecolor="#0d1117")
    gs = fig.add_gridspec(2, 2, width_ratios=[1.6, 1], height_ratios=[1, 1])
    ax_sp = fig.add_subplot(gs[0, :])
    ax_ch = fig.add_subplot(gs[1, 0])
    ax_tx = fig.add_subplot(gs[1, 1])
    for ax in (ax_sp, ax_ch, ax_tx):
        ax.set_facecolor("#0d1117")
        for sp in ax.spines.values():
            sp.set_color("#30363d")
        ax.tick_params(colors="#8b949e")

    sp = r["spectrum"]
    ax_sp.axvspan(*sp["bands"]["low"], color="#1f6feb", alpha=0.08)
    ax_sp.axvspan(*sp["bands"]["high"], color="#a371f7", alpha=0.08)
    ax_sp.plot(sp["rf"], sp["intensity"], color="#7ee8fa", lw=1)
    ax_sp.fill_between(sp["rf"], sp["intensity"], color="#7ee8fa", alpha=0.15)
    ax_sp.set_title("ID Sign-Wave", color="#e6edf3", loc="left")
    ax_sp.set_xlabel("relative frequency (rf)", color="#8b949e")
    ax_sp.set_xlim(0, 100)
    ax_sp.set_ylim(0, 1.2)
    ax_sp.text(1, 1.12, "LOW BAND · field device", color="#58a6ff", fontsize=8)
    ax_sp.text(31, 1.12, "HIGH BAND · lab (ID)", color="#d2a8ff", fontsize=8)
    if not r["past_threshold"]:
        ax_sp.text(50, 0.6, "Below Luminans threshold — no signature",
                   color="#f85149", ha="center")

    lim = max(100, r["resultant"]["magnitude"] * 1.1)
    ax_ch.set_xlim(-lim, lim)
    ax_ch.set_ylim(-lim, lim)
    ax_ch.set_aspect("equal")
    ax_ch.axhline(0, color="#30363d")
    ax_ch.axvline(0, color="#30363d")
    q = lim * 0.6
    for (x, y, name) in [(-q, q, "Materiatic"), (q, q, "Allurate"),
                         (-q, -q, "Exultate"), (q, -q, "Karmatic")]:
        ax_ch.text(x, y, name, color="#484f58", ha="center", va="center")
    ax_ch.text(0, lim * 0.95, "Afferent", color="#8b949e", ha="center", va="top", fontsize=8)
    ax_ch.text(0, -lim * 0.95, "Efferent", color="#8b949e", ha="center", va="bottom", fontsize=8)
    ax_ch.text(-lim * 0.95, 0, "Insular", color="#8b949e", va="bottom", fontsize=8)
    ax_ch.text(lim * 0.95, 0, "Alteral", color="#8b949e", ha="right", va="bottom", fontsize=8)
    for c in r["categories"]:
        col = "#f0883e" if c["peak"] else "#3fb950"
        ax_ch.plot([0, c["x"]], [0, c["y"]], color=col, lw=1.5, alpha=0.8)
        ax_ch.text(c["x"] * 1.08, c["y"] * 1.08, c["name"], color=col,
                   fontsize=7, ha="center", va="center")
    R = r["resultant"]
    ax_ch.annotate("", xy=(R["x"], R["y"]), xytext=(0, 0),
                   arrowprops=dict(arrowstyle="->", color="#f778ba", lw=2.5))
    ax_ch.plot(R["x"], R["y"], "o", color="#f778ba")
    ax_ch.set_title("I/A/E chart", color="#e6edf3", loc="left")

    ax_tx.axis("off")
    ax_tx.text(0, 1, summary_text(r), color="#e6edf3", va="top",
               family="monospace", fontsize=8.5, wrap=True)

    fig.tight_layout()
    fig.savefig(out_path, dpi=130, facecolor=fig.get_facecolor())
    plt.close(fig)


def main(argv=None):
    import argparse
    p = argparse.ArgumentParser(description="ID Sign-Wave generator")
    p.add_argument("subject", nargs="?", help="subject JSON file")
    p.add_argument("--out", default="signwave.png", help="output image path")
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
        plot(r, a.out)
        print(f"\nSaved {a.out}")
    except ImportError:
        print("\n(matplotlib not installed: pip install matplotlib to save the image)")


if __name__ == "__main__":
    main()
