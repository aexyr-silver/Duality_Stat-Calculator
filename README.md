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
pip install matplotlib            # only needed for images
python luminograph.py                          # built-in example -> overview.png + stack.png
python luminograph.py subject.json             # your subject
python luminograph.py subject.json --transparent              # + transparent A and D PNGs
python luminograph.py subject.json --transparent --colour "#ffffff"
python luminograph.py subject.json --json      # full result as JSON
python luminograph.py --example > my_subject.json
```

Outputs:
- `overview.png`: A (composite), D (radial), I/A/E chart, reading
- `stack.png`: C (component stack, developer view)
- with `--transparent`: `overview_composite.png` and `overview_radial.png`, wave only on a transparent background

## Web page features

- **Header:** pick a saved subject, edit its name and ID, generate a **New ID**, and **Save** (an orange dot means unsaved changes).
- **Subjects…** opens the subjects window: a table of every saved subject with its stage, I/A/E quadrant and status, plus **Open**, **Duplicate** (gets a new ID), **Export** and **Delete** for each. **New subject**, **Import JSON** (one subject or a list) and **Export all** are at the top. The list is kept in your browser between visits; use Export all to move it elsewhere.
- **Left panel:** the open subject's stats and desires only.
- **A · Composite Sign-Wave** (game UI), **D · Radial print**, **I/A/E radar chart**, **Reading**.
- **Transparent PNG export** of A (2400×600) and D (1600×1600), in any colour.
- **Developer view:** C · Component stack (collapse it to make the page faster).

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
| `drift_t` | Time value for pre-awakening desire drift |
| `desires` | All 16 desires, 1–100 |

## Rules implemented

- **Luminans threshold** = volume (L) × 1,000,000 ÷ 5 × 1e-5 units (≈140 for 70 kg). Below it: no ID Sign-Wave.
- **Stages** by capacity %: Normal (<5), The Veratia (5–9), The Vitia (10–25), The Reckoning (26+).
- **Categories** = average of their two desires. A category **peaks** above 80.
- **I/A/E position** = vector sum of the 8 categories, each pointing in its fixed direction.
- **Evocation** when past the Luminans threshold **and** either at The Reckoning, or at The Vitia with at least one peak.
- **Outcome**: control ≥ required control → Lumenborn (Proto-Human) / Stellaborn (Neo-Human); otherwise Desir.

## How the ID Sign-Wave is built

The wave is a sum of sine waves (frequency in rf = cycles per sample period):

- **Dominant** (low band): flow sets the frequency (afferent = slower, efferent = faster); scope sets the shape (insular = one wave, alteral = two close waves that beat against each other); height shows how far past the threshold.
- **Categories** (low band): one wave per category; height = category value; starting phase = the category's I/A/E direction angle.
- **Fine lines** (high band): 32 waves whose frequencies and phases come from the ID number. They are the same from the first emission to the permanent wave.
- **Pre-awakening drift:** before awakening, each desire wanders up to ±3 around its entered value (`DRIFT_AMPLITUDE`). This moves the I/A/E position and the dominant and category waves. Peaks and the Evocation trigger always use the entered values. After awakening, nothing drifts.
- **Instability**: high-frequency texture. Its strength comes from **control** (control 100 = smooth, control 1 = slightly rough; `NOISE_STRENGTH`). **Desir** get extra roughness on top (`DESIR_ROUGHNESS`). The pattern is seeded by the ID number.

The radial print (D) rounds each frequency to whole cycles so the loop closes.

## Placeholders to revisit

All are constants at the top of `luminograph.py`:

- Control formula: `required = 30 + 50 × chaos + 5 × (extra peaks)`.
- **Chaos** measures how much the above-average categories pull in different directions (0 = one clear pull, 1 = fully opposed).
- Band ranges and line counts.
