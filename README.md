# Luminograph — ID Sign-Wave generator

Generates a subject's **Identifying Signature Wavelength (ID Sign-Wave)** and I/A/E chart reading from their base stats, for Project Duality.

## Files

| File | Purpose |
|---|---|
| `luminograph.py` | All the logic. Runs on your computer, and the web page runs this same file in the browser. |
| `index.html` | Interactive page with sliders (for GitHub Pages). |
| `subject.json` | Example subject. |

## Run locally (Python)

```bash
pip install matplotlib            # only needed for the image
python luminograph.py                         # uses the built-in example
python luminograph.py subject.json --out signwave.png
python luminograph.py subject.json --json     # full result as JSON
python luminograph.py --example > my_subject.json
```

## Publish on GitHub Pages

1. Put `index.html` and `luminograph.py` in the root of a repository (same folder).
2. In the repository: **Settings → Pages → Build and deployment → Deploy from a branch**, choose your branch and `/ (root)`.
3. Open the Pages URL. The first load takes a few seconds while the Python engine (Pyodide) downloads.

To preview the page on your own computer, opening `index.html` directly won't work (browsers block loading `luminograph.py` from a file). Run a small local server in the folder instead:

```bash
python -m http.server 8000
```

then open `http://localhost:8000`.

## Subject fields

| Field | Meaning |
|---|---|
| `id` | Unique ID number; seeds the fine lines (high band) |
| `origin` | `Proto-Human` or `Neo-Human` |
| `mass_kg` | Mass; volume = mass ÷ 1.01 kg/L |
| `returnite_units` | Returnite currently held |
| `max_capacity_units` | Maximum capacity (100%) |
| `control` | 1–100; decides the Evocation outcome (placeholder formula) |
| `drift_t` | Time value for pre-awakening drift |
| `desires` | All 16 desires, 1–100 |

## Rules implemented

- **Luminans threshold** = volume (L) × 1,000,000 ÷ 5 × 1e-5 units (≈140 for 70 kg). Below it: no ID Sign-Wave.
- **Stages** by capacity %: Normal (<5), The Veratia (5–9), The Vitia (10–25), The Reckoning (26+).
- **Categories** = average of their two desires. A category **peaks** above 80.
- **I/A/E position** = vector sum of the 8 categories, each pointing in its fixed direction.
- **Evocation** when past the Luminans threshold **and** either at The Reckoning, or at The Vitia with at least one peak.
- **Outcome**: control ≥ required control → Lumenborn (Proto-Human) / Stellaborn (Neo-Human); otherwise Desir.

## ID Sign-Wave layout (relative frequency, rf)

- **Low band (0–30 rf)**, read by the field device:
  - Dominant peak: position shows flow (afferent = lower rf, efferent = higher rf); shape shows scope (insular = single sharp peak, alteral = split doublet); height shows how far past the threshold.
  - Category comb: 8 lines, one per category, height = category value.
- **High band (30–100 rf)**, read in the lab: 32 fine lines whose positions come from the ID number. They drift before awakening and are fixed after.
- **Line width** shows instability: broad lines = unstable.

## Placeholders to revisit

All are constants at the top of `luminograph.py`:

- Control formula: `required = 30 + 50 × chaos + 5 × (extra peaks)`.
- **Chaos** measures how much the above-average categories pull in different directions (0 = one clear pull, 1 = fully opposed).
- Band ranges and line counts.
