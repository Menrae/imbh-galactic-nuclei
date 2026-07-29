# Phase 5: SMBH-mass generalization scan

**Date**: 2026-07-28. **Script**: `scripts/phase5_smbh_mass_scan.py` (full design rationale
in its docstring and `paper/limitations.md#phase5-smbh-mass-scan`). **Data**:
`results/phase5_raw/summary.csv` (112 rows) + per-run pickles in `results/phase5_raw/`.

## Question

N26's second explicit open question (Section 5.4, alongside the sharp-vs-gradual threshold
question Phase 4 answered): does the paper's result — that a sufficiently massive initial BH
population (H18) reliably produces IMBHs via stellar collisions and GW capture — generalize to
galaxies with central black holes of other masses, or is it a Milky Way-specific coincidence?

## Design (recap; full detail in the design docs above)

- 7 $m_{\rm smbh}$ points, log-spaced over 3 decades, centered on and including N26's own
  fiducial $4\times10^6\,M_\odot$ exactly: $1.264911\times10^5$, $4\times10^5$,
  $1.264911\times10^6$, $4\times10^6$, $1.264911\times10^7$, $4\times10^7$,
  $1.264911\times10^8\,M_\odot$.
- Cluster structure ($\rho_0$, $r_0$, $n_0$, $R_h$, $\alpha_\star$, $\alpha_{\rm BH}$) held
  fixed at N26's Milky Way-specific values — **our own extension, not from N26** (Gate 1c). This
  isolates the pure dynamical effect of $m_{\rm smbh}$ from the separate, unresolved question of
  how a real galaxy's density profile would scale with SMBH mass.
- Mass distribution: H18 (N26's own literal IC, 0% primordial binaries), the one of the four
  ICs that actually produces IMBHs at the Milky Way mass.
- Both Eq. 22 `relaxation_mass_weighting` readings (`star_only`, `bh_inclusive`), per this
  project's standing convention.
- 8 seeds/point from the start (0-7) — per `paper/methodology.md` Gate 3, this compares directly
  against the already-validated Phase 3 $m_{\rm smbh}=4\times10^6$ anchor, so the $\ge$8-seed bar
  applied immediately.
- $7\times2\times8=112$ runs. Two quantities recomputed per grid point (not held fixed):
  `coulomb_log`$=\ln(m_{\rm smbh})$, and `a_min_pc`$=\max($`A_MIN_PC_DEFAULT`$,$
  `a_min_safety_bound`$(m_{\rm smbh}))$ — see the design docs for why the naive version of the
  latter broke (a real smoke-test hang, not a hypothetical).

All 112 runs completed (no exceptions); 11 hit the adaptive integrator's 2,000,000-step ceiling
before reaching 10 Gyr — tracked as data (`hit_step_ceiling`), not discarded, per the explicit
decision logged at the end of the previous session.

## Headline finding 1: the qualitative Eq. 22 dependence generalizes across 3 decades of SMBH mass

| reading | pooled any-IMBH (any BH $>100\,M_\odot$) | pooled mean pct $>100\,M_\odot$ |
|---|---|---|
| `star_only` | **56/56 (100%)** | 5.38% |
| `bh_inclusive` | 36/56 (64%) | 0.15% |

Under `star_only`, **every single one of the 56 runs** (all 7 $m_{\rm smbh}$ points $\times$ 8
seeds) produced at least one IMBH — a fully saturated existence claim (Gate 3 needs no
refinement here: 56/56 at a hard ceiling is as strong as this kind of evidence gets). Under
`bh_inclusive`, the *continuous* statistic N26 and Phase 3/4 use for headline comparisons
(mean % of the population $>100\,M_\odot$) stays below 0.5% at **every single grid point**,
across the full 3-decade range — the qualitative "`bh_inclusive` suppresses IMBH formation"
finding from Phase 3/4 (established at one SMBH mass) holds up at every mass tested here, not
just the Milky Way's.

**This directly answers N26's own Section 5.4 question, conditionally**: yes, the paper's
qualitative result (H18 produces IMBHs; the alternate Eq. 22 reading suppresses them) is *not*
a Milky Way-specific coincidence — it generalizes across 3 decades of SMBH mass, within this
scan's explicit scope (fixed cluster structure, our own extension per Gate 1c). Framed per Gate
8: the answer to N26's own open question is contingent on the same still-open Eq. 22 ambiguity
already documented in Phase 3/4, now shown to matter just as much across SMBH mass as it did at
a single mass.

**Secondary observation, not elevated to a result**: `bh_inclusive`'s *strict binary* indicator
(did any single BH cross 100 $M_\odot$, out of 1000) is nonzero more often than the near-flat
continuous statistic suggests — 36/56 pooled, ranging noisily from 2/8 (lowest mass) up to 8/8
(highest mass) per point, with no clean monotonic trend (e.g. the $1.26\times10^7\,M_\odot$
point drops to 3/8, lower than both neighbors). This is consistent with — not a revision of —
Phase 4's own finding that the strict binary indicator is occasionally nonzero even at its
"flat 0.0%" continuous points (0.1-0.3% marginal cases were already noted there). Left as an
observation (Gate 2/3 not cleanly cleared for a magnitude claim on this specific sub-statistic)
rather than a stated result.

**Gate 6 cross-check**: the $m_{\rm smbh}=4\times10^6$/`star_only` grid point reproduces Phase
3's own H18 validation **bit-for-bit** for seeds 0-2 (mergers 1102/1041/923 vs. Phase 3's
923-1102 range; max mass 75,052/9,181/89,870 vs. Phase 3's 9,181-89,870 range, mean 58,034 —
exact match). `coulomb_log` (15.201805) and `a_min_pc` (0.001) at this point both reduce to
exactly the Phase 3/4 defaults, as designed.

## Headline finding 2: a severe, non-monotonic runaway-growth "sweet spot" — scoped tightly to this scan's own design choice

The `hit_step_ceiling` rate under `star_only` is **not** a monotonic function of $m_{\rm smbh}$:

| $m_{\rm smbh}$ ($M_\odot$) | ratio to anchor | ceiling-hit rate (Wilson 95% CI) | mean max mass ($M_\odot$) | max max mass ($M_\odot$) |
|---:|---:|---:|---:|---:|
| $1.26\times10^5$ | $\times 0.032$ | 0/8, 0% [0, 32] | 4,326 | 26,903 |
| $4\times10^5$ | $\times 0.1$ | **4/8, 50% [22, 79]** | **2,555,496** | **5,047,452** |
| $1.26\times10^6$ | $\times 0.316$ | **7/8, 87.5% [53, 98]** | **2,782,188** | **4,910,523** |
| $4\times10^6$ (anchor) | $\times 1$ | 0/8, 0% [0, 32] | 27,132 | 89,870 |
| $1.26\times10^7$ | $\times 3.16$ | 0/8, 0% [0, 32] | 386 | 639 |
| $4\times10^7$ | $\times 10$ | 0/8, 0% [0, 32] | 173 | 257 |
| $1.26\times10^8$ | $\times 31.6$ | 0/8, 0% [0, 32] | 141 | 166 |

The non-convergence problem — and the underlying catastrophic growth driving it — is
concentrated entirely in a band roughly **3-10x below** the Milky Way anchor mass
($4\times10^5$-$1.26\times10^6\,M_\odot$), **not** at the lowest mass tested. At
$m_{\rm smbh}=4\times10^5$ and $1.26\times10^6$, the mean maximum BH mass reaches into the
**millions of solar masses** — in several individual runs, literally **exceeding the central
SMBH's own mass** (`max_mass` up to $5.05\times10^6\,M_\odot$ at $m_{\rm smbh}=4\times10^5$,
where the SMBH itself is only $4\times10^5\,M_\odot$). This is roughly 100-1000x more severe
than the already-documented runaway-growth residual at the anchor mass itself (mean 27,132,
consistent with the bit-for-bit Phase 3 reproduction above), which was already flagged as an
open, unresolved issue (`paper/limitations.md#phase2-emri-rate-high`).

### Mechanism (Gate 4)

Two $m_{\rm smbh}$-dependent effects compete, both traceable to specific equations already in
this codebase:

- **Relaxation-driven EMRI removal weakens as $m_{\rm smbh}$ drops.** Eq. 22's
  $t_{\rm relax}\propto\sigma^3$, and $\sigma\propto\sqrt{M_\bullet}$ (Eq. 1) — so
  $t_{\rm relax}\propto M_\bullet^{1.5}$: lower SMBH mass means *shorter* relaxation time,
  meaning *faster*, not slower, relaxation-driven diffusion into EMRI. Measured directly: mean
  EMRI fraction under `star_only` rises monotonically as $m_{\rm smbh}$ falls, from 7.8% at
  $1.26\times10^8$ up to **97.7%** at $1.26\times10^5$ (the weaker $\ln\Lambda=\ln(m_{\rm
  smbh})$ dependence on `coulomb_log` pulls the same direction but far more weakly, being
  logarithmic).
- **Growth-channel efficiency also rises as $m_{\rm smbh}$ (hence $\sigma$) drops.** Both
  growth channels' cross-sections scale inversely with $\sigma$ — Eq. 18's gravitational-
  focusing term $\propto 1/\sigma^2$, and the GW-capture cross-section's mass-dependence
  (already traced in `#phase2-emri-rate-high` as the source of the anchor-mass runaway) is
  similarly boosted at lower relative velocities.

These pull in *opposite* directions as $m_{\rm smbh}$ decreases, and the balance is not
monotonic: at the very lowest mass tested ($1.26\times10^5$), EMRI removal wins outright
(97.7% of the population is captured into EMRI, typically before a BH has time to accumulate
many merger generations — mean max generation 92.5, vs. thousands at the sweet spot below).
In the $4\times10^5$-$1.26\times10^6$ band, relaxation is weakened just enough that a
non-trivial fraction of trajectories escape early EMRI capture, at which point the already-
documented superlinear positive-feedback growth mechanism (Eq. 4-7's $A_{\rm cap}\propto
m_1^{12/7}$, Eq. 18's focusing term) takes over largely uncontested — mean max generation
reaches into the **thousands** (2235.5 at $4\times10^5$, one run reaching generation 7206).
Above the anchor, $\sigma$ grows large enough that both channels' efficiency drops fast enough
to suppress growth even though EMRI removal is by then comparatively weak (8-14% EMRI, but
mean max mass drops to a few hundred $M_\odot$) — i.e. the growth channels themselves become
inefficient, not just outcompeted by relaxation.

This is the same growth mechanism already independently verified in Phase 2/3
(`paper/limitations.md#phase2-emri-rate-high`) — not a new mechanism, but a large escalation
in its severity at a specific, non-obvious part of $m_{\rm smbh}$ parameter space.

### Falsification pass (Gate 5)

- **Not a step-ceiling artifact of the cap itself**: seed 7 at $m_{\rm smbh}=4\times10^5$
  completed in 1,139,059 steps (under the 2,000,000 cap) yet still reached max mass
  $1.56\times10^6\,M_\odot$ — the extreme growth is present in an uncapped run, not an
  artifact of how the ceiling truncates accounting.
- **Not a new bug**: the equations producing this growth (Eq. 4-7, Eq. 18) were independently
  verified against a direct high-resolution PDF re-render in the original Phase 2/3
  investigation and are unchanged here; only $m_{\rm smbh}$ (and its two required derived
  quantities) varies across this grid.
- **Genuinely non-monotonic, not a monotonic "colder cluster = worse" story**: the lowest-mass
  point tested ($1.26\times10^5$, colder still than the sweet-spot band) shows *zero* ceiling
  hits and a modest mean max mass (4,326) — ruling out the naive hypothesis that this is simply
  "runaway growth gets steadily worse as $m_{\rm smbh}$ decreases." The EMRI-removal mechanism
  above explains why the two effects cross at a specific band rather than one dominating
  everywhere.

### Scope statement (Gate 7) — this is not a claim about real low-mass galactic nuclei

This entire finding depends on the deliberate, explicitly-flagged design choice to hold the
cluster's structural profile fixed while varying only $m_{\rm smbh}$ (Gate 1c, `#phase5-smbh-
mass-scan`). A real galaxy with a $4\times10^5$-$1.26\times10^6\,M_\odot$ central black hole
plausibly has a correspondingly lower-density nuclear star cluster (e.g. via an
$M_\bullet$-$\sigma$ or $M_\bullet$-$N_\star$ relation) — which this scan does not attempt to
model. The catastrophic growth reported here (BHs reaching masses comparable to or exceeding
the central SMBH itself) is best read as **a signature of what "holding density fixed while
shrinking the SMBH" does to this specific model's dynamics**, not a prediction about real
lower-mass nuclei. It is, however, a genuine, mechanistically-explained, and heavily-evidenced
(8 seeds/point, clean 0% at both flanking points, 50-87.5% in the band, corroborated by
continuous `max_mass` data not just the binary ceiling flag) result about *this* scan as
designed.

**Grid resolution caveat**: the 7 points are log-spaced across 3 decades (a factor of
$\sim3.16$ between adjacent points) — precise enough to state that the severe-growth band sits
somewhere within $[4\times10^5,\ 1.26\times10^6]\,M_\odot$ and is absent at $1.26\times10^5$
and at/above $4\times10^6$, but **not** precise enough to locate exact boundaries finer than
that spacing. A finer grid in this specific band is a natural follow-up if this result
motivates one, but is not pursued here (consistent with the project's current focus on closing
out N26's two stated Section 5.4 questions rather than further refinement passes).

## Gate scorecard

| Gate | Finding 1 (generalization) | Finding 2 (sweet-spot runaway) |
|---|---|---|
| 1. Source grounding | Pass — N26 Sec. 5.4 open question (b), fixed-structure choice explicitly labeled (c) | Pass — mechanism traced to Eq. 1/18/22/4-7, all previously sourced; fixed-structure choice labeled (c) |
| 2. Noise floor | Pass — 56/56 and near-zero-everywhere both far exceed Phase 3's ~30-40% seed noise | Pass — 0% vs 50-87.5% with n=8/point, corroborated by continuous `max_mass`, not just the binary flag |
| 3. Sample size | Pass — fully saturated existence claim, no refinement needed | Pass at the sampled points (n=8 clears the bar); grid *resolution* (not seed count) is the limiting factor, flagged in scope |
| 4. Mechanism | Pass — $\sigma^3$/$\sigma^{-2}$-type scalings from Eq. 1/18/22, both already-used equations | Pass — competing $M_\bullet^{1.5}$ (relaxation) vs. $\sigma^{-2}$-ish (growth channels) scalings |
| 5. Falsification | Pass — bit-for-bit Gate 6 anchor match rules out a plumbing bug | Pass — uncapped run shows same extreme growth; not step-ceiling artifact; non-monotonic shape rules out naive "colder = worse" |
| 6. Consistency cross-check | Pass — anchor point bit-for-bit matches Phase 3 | Pass — anchor point's own (already-known) runaway is present at the same order of magnitude as Phase 3 (seeds 0-2 individually bit-for-bit identical, 9,181-89,870; the fuller 8-seed mean of 27,132 is lower than Phase 3's 3-seed mean of 58,034 simply because seeds 3-7 add lower values, not a discrepancy) |
| 7. Scope statement | Pass — explicitly scoped to H18, fixed structure, both Eq. 22 readings | Pass — explicitly scoped as a consequence of the fixed-structure choice, not a real-galaxy claim; grid resolution caveat stated |
| 8. Framing | Pass — "the answer to N26's open question is contingent on X," not a claim N26 is wrong | Pass — framed as our own scan's behavior, not a claim about real nuclei |
| 9. Reproducibility | Pass — `scripts/phase5_smbh_mass_scan.py` + `results/phase5_raw/summary.csv` + per-run pickles | (same) |

Both findings clear all 9 gates and graduate to results.

## Caveats

- As with every Phase 3/4/5 result, the Eq. 22 $\langle M_{\rm avg}\rangle$/$\rho$ ambiguity
  remains genuinely open (`paper/limitations.md#average-object-mass`) — both readings are
  reported throughout this document specifically because of that, not resolved by this scan.
- The fixed-cluster-structure choice (Gate 1c) is this scan's single biggest scope limitation;
  see Finding 2's scope statement above.
- $a_{\rm min}$ safety-bound clamping (see design docs) means the innermost sampling radius is
  slightly more conservative than the raw `a_min_safety_bound` formula at high $m_{\rm smbh}$ —
  flagged there, not revisited here.
- 11/112 runs (all `star_only`, all in the $4\times10^5$-$1.26\times10^6$ band) did not reach
  10 Gyr before hitting the step ceiling; their reported `max_mass`/`n_mergers`/etc. reflect
  partial integration (typically 1-9 Gyr, see per-seed detail above), not the full 10 Gyr window
  — a downward bias on how extreme the true (uncapped) endpoint would be, not an upward one.
