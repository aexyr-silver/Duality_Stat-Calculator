# I/A/E Classification — Reference Sheet

*Project Duality · Magic System · Working reference (updated 3 Nov 2026)*

Status key: **[Decided]** = confirmed by Mysten · **[Proposed]** = suggested, not yet confirmed · **[Draft]** = placeholder, open to change · **[Open]** = undecided

---

## 1. Returnite Detection

**[Decided]**
- Returnite is detected through the emission of its **Luminans factor** wavelength.
- It can also be detected in blood via the ratio of normal vs Returnite-affected cells. This gives the number of Returnite units already in the body.
- Wavelengths are visualized as **Luminographic Prints**. Taking a Print requires the subject to stimulate their core desire.

### Instruments **[Decided]**

| | Field device | Lab equipment |
|---|---|---|
| Size | Small, portable | Large, fixed |
| Range | Wider | Close range |
| Accuracy | Lower | Higher |
| Band read | **Low frequency** | **High frequency** (plus low) |
| Shows | Presence, I/A/E position, amplitude | Fine lines (individual ID) |

---

## 2. Luminans Threshold

**[Decided]**
- 1 Luminans = 1e-5 units of Returnite in 5 mm³ of organic material.
- A signature forms only once the whole body reaches 1 Luminans per 5 mm³. Below that, there is no signature; Returnite only disrupts circadian rhythms.
- The threshold scales linearly with body volume. Volume is deduced from mass; tissue density differences are ignored because Returnite spreads evenly.
- Average human density ≈ **1.01 kg/L** → ≈ **1.98 units per kg**.
- **Average 70 kg human threshold: ≈140 units.**
- The threshold can fall anywhere on the capacity percentage scale, depending on the creature's maximum capacity.

---

## 3. Capacity and Stages

**[Decided]**
- Each individual has a different maximum Returnite capacity (100%).
- **Percentage of capacity** is the only measure that compares individuals.
- Example: 100 units held of a 1,000-unit maximum = 10%.

| Capacity | Stage | Description |
|---|---|---|
| 0% | Normal Human | No symptoms |
| 5–9% | **The Veratia** | Mild symptoms; craves more Returnite |
| 10–25% | **The Vitia** | Visibly sickly features, signs of withdrawal. More Returnite does not help; it pushes one into the next phase. May also begin the Evocation when one or two desires are stimulated beyond their threshold (above 80) |
| 26%+ | **The Reckoning** | Immediately enters **the Evocation** |

**[Decided]** At high exposure, desire still shapes the *form* of the mutation; only the outcome leaves the subject's control.

---

## 4. The Evocation and Its Outcomes

**[Decided]** The Evocation is the awakening process.

| Origin | Successful Evocation | Failed Evocation |
|---|---|---|
| Proto-Human | **Lumenborn** | **Desir** |
| Neo-Human | **Stellaborn** | **Desir** |

- **Success or failure** depends on the control one has over their desire. Regulating one's energy into a stable rhythm (however messy, as long as it is stable) lets one retain sentience and succeed.
- **Desir** (monsters of desire): can only crave the satisfaction of their desires. They lose all sentience.
- **[Decided]** Neo-Humans fluctuate across the A/E spectrum without settling until a trigger (high desire) awakens them.

---

## 5. Desires and the Core

**[Decided]**
- **Base stats:** the 16 basic human desires, each rated 1–100.
- **Core stat:** the 1 or 2 desires that peak compared to the rest (above 80). They cause awakening.
- After awakening, the wavelength stops shifting and becomes a **permanent ID** for that person or monster.
- A unique ID number produces each subject's fine lines. The ID fine lines **never change**: they are the same from first emission to the final permanent wavelength.
- **Before awakening, the desires drift.** This shifts the I/A/E position and the desire-driven parts of the wave. After awakening, the desires stop drifting and the whole wavelength is permanent.
- **[Decided]** In the code, each desire drifts up to ±3 around its entered value (before being combined into the 8 categories); peaks and the Evocation trigger use the entered values.
- **[Decided]** Wave instability comes from **control**, with the pattern seeded by the ID: low control = unstable (rough) wave, high control = stable (smooth) wave. The control-based roughness is kept subtle; **Desir** get extra roughness on top.

### Desire Categories (game stats) **[Decided]**

The 16 desires are grouped into 8 categories, used as stat types in the game.

| Category | Desires |
|---|---|
| **DOMINION** | Power + Status |
| **SOVEREIGNTY** | Independence + Honor |
| **CORPOREALITY** | Eating + Physical Exercise |
| **KINSHIP** | Family + Social Contact |
| **SERENITY** | Tranquility + Acceptance |
| **DEVOTION** | Romance + Idealism |
| **HIERARCHY** | Vengeance + Order |
| **VORACITY** | Curiosity + Saving |

Note: Dominion (being above others) and Hierarchy (competing for rank, keeping order) both involve rank; in-game descriptions should distinguish them.

**[Decided]**
- The awakening rule (1–2 peaks) applies to the **8 categories**.
- The code takes the **16 desires** as input; each category = the sum of its two desires. In-world lore uses the 8 categories.
- Each category has a **vector (direction) from the centre** of the I/A/E chart; its value sets the magnitude in that direction.

**[Decided]** Peak threshold: a category peaks when the **average** of its two desires is above **80**.

**[Decided]** Category directions (45° apart):

| Direction | Category |
|---|---|
| Afferent pole | **Serenity** |
| Efferent pole | **Hierarchy** |
| Insular pole | **Corporeality** |
| Alteral pole | **Dominion** |
| I-A (Materiatic) | **Voracity** |
| A-A (Allurate) | **Kinship** |
| I-E (Exultate) | **Sovereignty** |
| A-E (Karmatic) | **Devotion** |

Opposite pairs: Serenity ↔ Hierarchy · Corporeality ↔ Dominion · Voracity ↔ Devotion · Kinship ↔ Sovereignty.

**[Decided]** A person's characteristic I/A/E position is the **vector sum of all eight** category vectors; each vector's length (distance from the centre) is that category's magnitude. Opposed categories cancel toward the centre.

### Returnite Flow (ReF) system **[Decided]**
- The Luminans Factor is quantified at 1e-5 units per 5 mm³ and characterized by the 8 categories within the I/A/E chart.
- Each desire affects the reading of a person's **Returnite Flow (ReF) system**.
- The **Luminans core** emits the **Identifying Signature Wavelength**.
- **Energy meridian vessels (EMV)** work like capillaries across the body, carrying Returnite from and back to the core.

### Quadrant shorthand **[Decided]** (scope letter first, flow letter second)

| Code | Quadrant |
|---|---|
| I-A | Materiatic (Insular + Afferent) |
| A-A | Allurate (Alteral + Afferent) |
| I-E | Exultate (Insular + Efferent) |
| A-E | Karmatic (Alteral + Efferent) |

### Luminans Core **[Decided]**
- Forms at awakening. Its position can be anywhere in the body.
- Typical humans and creatures have one; more cores are theoretically plausible.
- Returnite with a permanent signature tries to overcome any systemic invasion by devouring alien energy at the core.
- **Detection:** a small trace of foreign energy is inserted. The system's flow stays undisturbed, but the foreign energy disappears (and can no longer be detected) where the core is.
- Alteral-based powers cannot directly alter the core. They can temporarily affect the "symptoms" around the "cause."
- If the core runs out of energy, it triggers **Limit Break** (working name; to be renamed).

---

## 6. The Two Axes

**[Decided]**

| Axis | Poles | Meaning |
|---|---|---|
| **Flow** (casually "A/E") | **Afferent ↔ Efferent** | Absorbs inward ↔ projects outward |
| **Scope** | **Insular ↔ Alteral** | Acts on self/world ↔ acts through other people |

- "I/A/E" names both the spectrum and the subject's signature reading. It applies only to subjects past their Luminans threshold.
- **Cosmological basis:** afferent = contraction-dominant (cf. Dark Stellae), efferent = expansion-dominant (cf. Nebulae), per the First Light / Great Wave consensus.
- **Equilibrium mechanism:** Returnite restores balance and fills its container equally. A strong desire acts as a gradient; Returnite flows to correct it. A held, steady desire lets the energy settle into a fixed channel. An uncontrolled desire leaves it continually "correcting" the body, which is degradation.

---

## 7. Quadrants

**[Decided]**

| | **Insular** | **Alteral** |
|---|---|---|
| **Afferent** | **Materiatic** (pl. *Materiatices*) | **Allurate** (pl. *Allurae*) |
| **Efferent** | **Exultate** (pl. *Exultae*) | **Karmatic** (pl. *Karmatices*) |

The suffixes run along the diagonals (opposite quadrants share an ending). **[Open]** whether this is in-world convention.

Desire placement is now set by the 8 category directions (see Section 5, Desire Categories). The earlier per-desire draft placement is superseded.

---

## 8. Signature Wavelength

**[Decided]**
- Each subject's signature is unique.
- **Low-frequency band:** travels far and passes through tissue, but is coarse. Carries the dominant peak (I/A/E position) and amplitude. Read by the field device.
- **High-frequency band:** short range, fine detail. Carries the fine lines (individual ID). Needs lab equipment at close range.

**[Decided]** The ID Sign-Wave is a sum of sine waves (see Section 9 for the build): category waves (low band, driven by the 8 categories), ID fine lines (high band, fixed by the ID), and an instability texture (from control, extra for Desir). Shown in the game UI as the scrolling **ID Sign-Wave** and the circular **ID Print**.

---

## 9. Signature Generator (code)

**[Decided]** Build `luminograph.py` (runs locally) plus an `index.html` for GitHub Pages that runs the same Python in the browser.
- **Inputs:** ID number, 16 desires (1–100), mass (kg), current Returnite units, maximum capacity units.
- **Outputs:** volume, threshold, capacity %, stage, awakening status, I/A/E position and quadrant, waveform, visualization.

**[Decided]**
- Awakening needs one or more peaking categories plus enough Returnite. More peaks make the vector sum more chaotic, so the stability needed is harder to reach.
- A subject can sit in The Veratia or The Vitia below their Luminans threshold; some never evolve.
- A **control** stat (1–100) decides the outcome (formula to be discussed).
- The wave is the **Identifying Signature Wavelength (ID Sign-Wave)**; frequency axis uses placeholder "relative frequency (rf)".

**[Decided] Visualization:** A · Composite Sign-Wave (time on x, ± amplitude on y) for the game UI; D · Radial print also available; C · Component stack for developer use. No spectrogram or frequency spectrum in the UI. The web page imports/exports subjects as JSON and saves transparent PNGs of A and D.

**[Decided] Rules in the generator**
- **Required control = 5 + 50 × chaos + 5 × each peaking category.** Control at or above it → Lumenborn / Stellaborn; below → Desir.
- **Chaos (0–1):** how much the categories *above the subject's own average* pull in different directions. 0 = one clear pull; 1 = fully opposed. Below-average categories don't count.
- **The Evocation requires being past the Luminans threshold.** Someone at The Reckoning but below their threshold never enters it.
- **Desir keep a permanent ID Sign-Wave**, like any awakened subject.
- **Uncategorized:** if the total vector is shorter than 5% of the eight categories' combined length, the subject has no quadrant.

**[Decided] ID Sign-Wave build**
- No separate dominant wave.
- **Category waves:** one per category at fixed frequencies; height = category value; starting phase = the category's I/A/E direction angle.
- **ID fine lines:** 8 waves set by the ID number.
- **Instability texture:** 8 fast waves seeded by the ID; strength = instability × 0.1 (instability from control), + 0.2 for Desir.
- **Drift:** ±3 per desire, each at its own speed.
- **Animation:** the Sign-Wave scrolls 3% of its window per second.

**[Open]**
- Overall wave height (currently grows with how far past the threshold the subject is, levelling off at 10×) — to discuss.
- Frequency unit — no unit shown; internals to discuss.

---

## 10. Other Open Items

- Name of the map/spectrum chart
- Name of the centre (equilibrium point)
- Final placement of the 16 desires
- How MC forms (Human → Mutated → Transformed → Evolved) align with the stages

### Name candidates (for later)
- **Map:** Spectrum Cupiditatis, Votive Chart, Luminans Field, Appetence Map, Desiderium Index
- **Centre:** Aequor, Libra Point, Quies, Null Point
- **Intensity:** Ardor, Fervor, Magnitude
