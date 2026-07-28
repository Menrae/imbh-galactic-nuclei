# Finding validation protocol

This project routinely produces two kinds of output: (1) validation against N26's own
published numbers (Table 1), where the standard is straightforward agreement/disagreement,
and (2) **secondary findings** — patterns we discover in our own simulation output that go
beyond reproducing a published number, including some that surface genuine ambiguities or
apparent inconsistencies in N26's own text (see `paper/limitations.md` throughout). The
second kind needs its own bar before it's written up as a *result* rather than logged as a
*preliminary observation* — both because a false-positive "finding" wastes downstream effort
built on it, and because several of these findings, if stated carelessly, would read as
accusations against the original authors' work rather than honest descriptions of where a
published paper (routinely, unremarkably) left something underspecified.

This document is the checklist. It codifies practices this project was already using
ad hoc (the Eq. 22 investigation in particular) as a named, repeatable protocol, so future
findings get the same rigor without reinventing the process each time.

## The gates

A pattern in simulation output must clear these before it's written up as a **result**
(stated as fact in `results/*.md`, `PROJECT_OVERVIEW.md`, or any eventual `paper/` writeup)
rather than logged as an *observation* (a candidate finding noted in `paper/limitations.md`
or a script's output, not yet asserted).

### Gate 1 — Primary-source grounding, three-way classification

Before any claim compares our result to N26 (or any cited source), classify it explicitly as
one of:

- **(a) N26 states X explicitly** — cite the specific page/section, ideally verbatim from a
  direct PDF read (not paraphrase, not memory of the abstract), and say whether our result
  matches or mismatches it.
- **(b) N26's text is genuinely ambiguous or underspecified about X** — cite *both* (or all)
  candidate readings verbatim, with their respective textual anchors. Never paraphrase an
  ambiguity into a single reading before presenting it.
- **(c) This is our own modeling choice or extension, not from N26 at all** — label it as
  ours, explicitly, so it can never be misread as a claim about what N26 says or does.

This is already this project's house style (every entry in `paper/limitations.md` does this);
this gate makes it a mandatory, named check rather than an instinct.

### Gate 2 — Effect size clears the measured noise floor

Compare the claimed effect against an *empirically measured* noise floor for that exact
statistic at the relevant sample size — never an eyeballed judgment that "this looks
different." This project already has real noise-floor measurements to use: e.g. Phase 3
found merger counts vary ~30-40% seed-to-seed at $N=1000$/3 seeds
(`results/phase3_validation_2026-07-26.md`). State the floor and the margin by which the
claimed effect clears it.

### Gate 3 — Sample size adequate for the specific claim being made

Distinguish two different kinds of claim, which need different amounts of evidence:

- **Existence claims** ("this effect happens / doesn't happen at all") can be established
  with few seeds if the effect saturates — e.g. Phase 4 pass 1's `bh_inclusive` finding
  (exact 0.0% across 8 mass points × 3 seeds = 24 runs) needed no further seeds; 24/24 at
  a hard zero is already about as strong as evidence gets.
- **Location/magnitude claims** ("the threshold sits at X") need enough seeds that a single
  flip doesn't set the reported number. Working rule adopted here: don't state a specific
  boundary location from fewer than ~8 seeds at the points bracketing it. (Phase 4 pass 1's
  25-32 M☉ band rested on a single 1-of-3 seed flip — exactly the case this gate exists to
  catch — and got a dedicated pass-2 refinement, `scripts/phase4b_threshold_refinement.py`,
  before being written up as a number.)

### Gate 4 — Mechanism, not just pattern

A numeric difference isn't a finding until there's a physical or mathematical mechanism,
traceable to the actual equations in play, that explains *why*. "These two config settings
give different numbers" is an observation; "the eviction-into-EMRI rate, set by Eq. 22's
$\rho\langle M_{\rm avg}\rangle$, controls whether a BH survives long enough for either
growth channel to operate" is a finding. If no mechanism can be articulated and traced to
specific equations/code, the pattern stays an observation, however statistically solid.

### Gate 5 — Falsification / adversarial pass

Before accepting a pattern, deliberately try to break it:

- Is it explained by a **mundane numerical artifact** (substep count, timestep safety
  factor, RNG stream, adaptive-timestep sizing) rather than physics? Test by varying the
  suspect numerical knob and checking the pattern survives — as was done for
  `relaxation_substeps` (1-2000, a 2000x range) during the Phase 2 EMRI-rate investigation.
- Is there a **simpler, boring explanation** (a bug) that should be ruled out first? Check
  before treating a discrepancy as scientifically interesting.
- Was a genuine attempt made to find a **middle ground** that would dissolve an apparent
  binary tension, rather than jumping straight to "these two extremes disagree, therefore
  X"? (`paper/limitations.md#phase2-emri-rate-high`'s "searching for a middle ground" pass —
  testing a rigorous multi-species weighting formula and finer substepping under
  `bh_inclusive` — is the template: both were tried, both failed to dissolve the tension,
  and that failure is itself part of the finding, not a gap in it.)

This gate doesn't require the pattern to *survive* every attack — sometimes the adversarial
pass finds the boring explanation, and the right outcome is a bug fix, not a finding. What's
mandatory is making the attempt and documenting what was tried, whichever way it goes.

### Gate 6 — Internal consistency cross-check

Whenever new code or a new scan overlaps a previously-validated result, confirm it
reproduces that prior result — ideally bit-for-bit under identical seeds — before trusting
the new numbers. Cheap, and catches silent plumbing bugs before they're baked into a
"finding." Example: Phase 4 pass 1's $m_{\rm max}=100$/`star_only` grid point is equivalent
by construction to a Phase 3 H18 run; 2 of 3 seeds matched Phase 3 bit-for-bit, and the third
seed's small divergence was traced to a specific, understood cause (a more precise
closed-form `mean_bh_mass`) rather than left as an unexplained discrepancy.

### Gate 7 — Explicit scope statement

State precisely which parameters were held fixed ($N$, $M_\bullet$, $\alpha_\star$,
primordial-binary fraction, $t_{\rm max}$, seed count, etc.) so the finding cannot be read
as a broader claim than what was actually tested. No implicit generalization — if Phase 5's
SMBH-mass scan hasn't run yet, a Phase 4 finding says nothing about other $M_\bullet$, and
should say so.

### Gate 8 — Framing discipline (the one that keeps this fair to N26)

This is the gate specifically aimed at not calling another paper's work into question
haphazardly. When a finding touches an ambiguity or apparent inconsistency in N26:

- Only use language implying an error after checking the discrepancy against the *original*
  source N26 itself cites — not just against our own expectation. The house precedent is
  `paper/limitations.md#eq21-exponent-discrepancy`: we don't say "N26 is wrong," we say
  "N26's printed exponent doesn't match its own cited source (Volonteri et al. 2013 Eq. 14),
  confirmed by direct PDF read of both," and flag it as unconfirmed with the authors.
- State plainly that under-specification in a published paper is normal, not evidence of
  carelessness — methods sections cite other work by design, and page limits routinely
  compress exact numerical prescriptions. `paper/limitations.md#coulomb-logarithm` and
  `#average-object-mass` both frame N26's silence this way, not as a defect.
- Prefer conditional framing: "the answer to N26's own stated open question depends on
  reading X vs. Y" rather than "N26's claim is incorrect." Phase 4's headline finding is
  written this way deliberately — N26 explicitly poses the threshold question as open future
  work (Section 5.4), so showing the answer is contingent on an ambiguity elsewhere in their
  own model is engaging with their stated question, not contradicting a stated claim.
- When multiple readings are textually defensible, report results under **all** of them, not
  just whichever makes the tidiest story. This is why Phase 4 was scoped, from the start, to
  run under both `relaxation_mass_weighting` settings rather than defaulting to one.

### Gate 9 — Reproducibility artifact

Every finding ships with the exact script that produced it, the raw per-seed CSV, and (for
runs expensive enough that regenerating them isn't trivial) pickled full results — committed
alongside the write-up, not described only in prose. Anyone (a reviewer, or a future version
of this project) should be able to rerun the exact scan.

## Graduation criteria

A pattern may be stated as a **result** (not merely an *observation*) once:

- Gates 1, 2, 4, 6, 7, and 9 are satisfied, **and**
- Gate 5 (falsification) has been genuinely attempted and its outcome documented, whichever
  way it went, **and**
- if the claim is a location/magnitude claim rather than a bare existence claim, Gate 3's
  ≥8-seed bar is met at the points that bracket it, **and**
- Gate 8's framing is applied throughout the write-up, unconditionally, whenever the finding
  touches N26's own text.

## Worked example: Phase 4's critical-mass-threshold finding

Scorecard, final (pass 1 `results/phase4_mass_threshold_scan_2026-07-27.md` +
pass 2 refinement, both folded into the same doc):

| Gate | Status | Note |
|---|---|---|
| 1. Source grounding | **Pass** | IMBH definition (b) and the threshold question itself (N26 Sec. 5.4) directly quoted from the PDF; the Eq. 22 ambiguity already carries its own three-way trace in `#average-object-mass`. |
| 2. Noise floor | **Pass** | `bh_inclusive`'s 0.0% is exact across every point — no floor to clear. `star_only`'s rise (0%→12.7%) is far larger than Phase 3's measured ~30-40% seed-to-seed merger-count noise. |
| 3. Sample size for the *location* claim | **Pass (after pass 2), claim corrected** | The 25-32 M☉ band rested on one 1-of-3 seed flip at $m_{\rm max}=25.3$. Pass 2 (`scripts/phase4b_threshold_refinement.py`, 8 seeds/point) didn't just tighten this — it overturned it: $m_{\rm max}=31.8$'s apparently-saturated 3/3 turned out to be 6/8 (75%, not saturated) once properly sampled. The graduated finding is "gradual crossover, ~20-32 M☉, not fully saturated even at the top," not the original "sharp-ish threshold at 25-32 M☉." This is Gate 3 doing exactly its job: catching a small-$n$ artifact before it shipped as a number. |
| 4. Mechanism | **Pass** | Survival time against EMRI ejection gates both growth channels; traced to the specific $t_{\rm relax}$ dependence in Eq. 22. |
| 5. Falsification | **Pass** | The underlying Eq. 22 tension already went through a dedicated adversarial pass (`#phase2-emri-rate-high`'s "searching for a middle ground") before Phase 4 began — multi-species weighting and finer substepping were both tried against the ambiguity and failed to dissolve it, which is itself part of why Phase 4 treats this as a structural fork worth scanning both ways rather than a bug to fix. |
| 6. Consistency cross-check | **Pass** | $m_{\rm max}=100$/`star_only` reproduced Phase 3's H18 run bit-for-bit in 2/3 seeds; the third seed's divergence was traced to a specific, understood cause. |
| 7. Scope statement | **Pass** | Explicitly scoped to $N=1000$, $M_\bullet=4\times10^6\,M_\odot$, $\alpha_\star=1.25$, primordial fraction 0, in both the results doc and this entry. |
| 8. Framing | **Pass** | Written as "the answer to N26's own open question depends on X," not as a claim N26 is wrong about anything. |
| 9. Reproducibility | **Pass** | `scripts/phase4_mass_threshold_scan.py` + `results/phase4_raw/summary.csv` (+ pickles) for pass 1; `scripts/phase4b_threshold_refinement.py` + `results/phase4b_raw/summary.csv` for pass 2. |

Only gate 3 was open after pass 1, and only for the *location* claim specifically — the
*existence-of-sensitivity* claim (the threshold's presence and rough shape differ between
readings at all) was already fully graduated. This is the expected pattern: existence claims
usually clear the bar cheaply, location/magnitude claims are where seed count matters most —
and, as this case shows concretely, that's not a formality: the specific number gate 3 was
gating turned out to be wrong, not just imprecise, once properly sampled. A finding that
"looks done" on 3 seeds is exactly the failure mode this gate exists to catch.
