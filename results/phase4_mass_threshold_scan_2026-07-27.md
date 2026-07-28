# Phase 4: critical initial-mass-distribution threshold scan (pass 1 + pass 2 + pass 3)

Run 2026-07-27. Log-uniform mass distribution on $[6, m_{\rm max}]\,M_\odot$ ($m_{\rm max}$
scanned over 9 log-spaced points, 16-100 $M_\odot$), $N=1000$ BHs, $M_\bullet=4\times10^6\,
M_\odot$, $\alpha_\star=1.25$, 10 Gyr, primordial-binary fraction fixed at 0, 3 seeds each
(0, 1, 2), **both** Eq. 22 $\langle M_{\rm avg}\rangle$/$\rho$ readings
(`relaxation_mass_weighting`). Design and reasoning: `paper/limitations.md#phase4-mass-family-scan`.
54 runs, 4.3 CPU-hours, ~0.54 hr wall-clock at 8 parallel workers (faster than the 1.5-2.5 hr
estimate — `bh_inclusive` runs turned out much cheaper than assumed, ~25-33s each, since they
never enter the runaway-growth regime).

**Headline finding: the threshold's existence and location are not robust to the Eq. 22
ambiguity.** Under `star_only`, IMBH formation turns on smoothly starting around
$m_{\rm max}\approx25$-$32\,M_\odot$ and grows steadily up to H18's own 12.7% at $m_{\rm
max}=100$. Under `bh_inclusive`, essentially **no** IMBH formation occurs anywhere in the
scanned range — even at $m_{\rm max}=100$ (exact H18), only 2/3 seeds produce a bare handful
of BHs marginally over 100 $M_\odot$ (0.1-0.3% of the population). This directly falsifies the
working assumption carried over from Phase 3 (`paper/limitations.md#phase2-emri-rate-high`,
final paragraph) that bulk-population statistics like "% BHs > 100 $M_\odot$" would be much
less sensitive to this ambiguity than the extreme max-mass tail — see "Revised understanding"
below.

> **UPDATE, 2026-07-28 (pass 2 refinement) — the "critical band" language above is
> superseded on the location claim specifically; the sensitivity/existence claim stands
> unchanged.** Per `paper/methodology.md`'s Gate 3 (a location claim needs more than 3
> seeds per point), a dedicated follow-up ran 8 seeds instead of 3 at 5 `star_only` grid
> points spanning this band (`scripts/phase4b_threshold_refinement.py`,
> `results/phase4b_raw/summary.csv`). Finding: **the pass-1 "band" undersold how gradual
> the transition actually is.** With more seeds, $m_{\rm max}=31.8$ — which pass 1's 3/3
> seeds made look fully saturated — turns out to produce *zero* IMBHs in 2 of 8 seeds
> (75%, 95% CI 41-93%, still not saturated). The "any IMBH forms" probability rises
> smoothly and without ever fully saturating across the whole tested band: 0/8 (0%) at
> $m_{\rm max}=20.1$, 3/8 (38%) at 22.6, 4/8 (50%) at 25.3, 6/8 (75%) at both 28.4 and
> 31.8 — see "Pass 2: the transition is gradual, not sharp" below for the full data and
> what this means for N26's own framing of the open question. Read the "critical band"
> language in the paragraph above as historical (what pass 1's thin sample suggested),
> not as the final answer.

## Results

| $m_{\rm max}$ [M☉] | $\langle m\rangle$ [M☉] | Reading | % BHs>100 (mean) | % BHs>100 (range) | Any seed >100? | Mergers (mean) | Max mass (mean) [M☉] |
|---:|---:|---|---:|---:|:---:|---:|---:|
| 16.0 | 10.2 | star_only | 0.00 | 0.0-0.0 | 0/3 | 30.0 | 49.1 |
| 20.1 | 11.7 | star_only | 0.00 | 0.0-0.0 | 0/3 | 39.7 | 75.0 |
| 25.3 | 13.4 | star_only | 0.07 | 0.0-0.2 | **1/3** | 56.7 | 121.4 |
| 31.8 | 15.5 | star_only | 0.30 | 0.1-0.4 | 3/3 | 82.7 | 185.9 |
| 40.0 | 17.9 | star_only | 0.87 | 0.5-1.1 | 3/3 | 118.3 | 369.1 |
| 50.3 | 20.8 | star_only | 1.67 | 1.5-2.0 | 3/3 | 175.3 | 1267.7 |
| 63.2 | 24.3 | star_only | 4.47 | 3.8-5.0 | 3/3 | 304.3 | 1872.8 |
| 79.5 | 28.5 | star_only | 7.43 | 6.8-8.1 | 3/3 | 508.7 | 6207.7 |
| 100.0 | 33.4 | star_only | 12.70 | 11.7-13.9 | 3/3 | 1060.3 | 36164.9 |
| 16.0 | 10.2 | bh_inclusive | 0.00 | 0.0-0.0 | 0/3 | 0.3 | 16.2 |
| 20.1 | 11.7 | bh_inclusive | 0.00 | 0.0-0.0 | 0/3 | 2.0 | 29.2 |
| 25.3 | 13.4 | bh_inclusive | 0.00 | 0.0-0.0 | 0/3 | 1.7 | 31.5 |
| 31.8 | 15.5 | bh_inclusive | 0.00 | 0.0-0.0 | 0/3 | 1.3 | 46.4 |
| 40.0 | 17.9 | bh_inclusive | 0.00 | 0.0-0.0 | 0/3 | 1.0 | 41.7 |
| 50.3 | 20.8 | bh_inclusive | 0.00 | 0.0-0.0 | 0/3 | 1.7 | 63.0 |
| 63.2 | 24.3 | bh_inclusive | 0.00 | 0.0-0.0 | 0/3 | 1.0 | 65.3 |
| 79.5 | 28.5 | bh_inclusive | 0.00 | 0.0-0.0 | 0/3 | 1.3 | 85.5 |
| 100.0 | 33.4 | bh_inclusive | 0.13 | 0.0-0.3 | 2/3 | 1.7 | 111.6 |

Raw per-seed data: `results/phase4_raw/summary.csv`; pickled `SimulationResults` per run
alongside it.

## Pipeline validation aside

The $m_{\rm max}=100$/`star_only` row is, by construction, equivalent to a Phase 3 H18 run
(primordial fraction 0, same log-uniform family, same seeds). Seeds 1 and 2 reproduce Phase 3's
H18 seed-1/seed-2 results **bit-for-bit** (merger count and max mass match to displayed
precision). Seed 0 diverges (1217 vs 1102 mergers, max mass 9444 vs 75052 $M_\odot$) —
traced to `mean_bh_mass`: this scan uses the log-uniform family's *exact* closed form
(33.4114, `initial_conditions.log_uniform_mean`) rather than Phase 3's Monte-Carlo-estimated
value (33.3962, N=2e6) — a genuine, tiny (0.045%) numeric difference that apparently crossed a
timestep-sizing decision boundary in seed 0's particular chaotic trajectory but not seeds 1/2's.
Not a bug: expected sensitivity of a chaotic adaptive Monte Carlo integrator to a small,
deliberately more-precise parameter change. Good evidence the scan pipeline reproduces Phase 3
correctly.

## Pass 2: the transition is gradual, not sharp (2026-07-28)

Run 2026-07-28, `scripts/phase4b_threshold_refinement.py`. Motivated by
`paper/methodology.md` Gate 3: pass 1's "critical band" rested on a single seed flipping
(1/3 at $m_{\rm max}=25.3$) — not enough to state a location. This pass adds 5 more seeds
(0-7, 8 total) at the 3 shared pass-1 grid points in the band plus 2 new geometric-midpoint
points, `star_only` only (see file docstring for why `bh_inclusive` didn't need this — its
finding was already saturated at 24/24 runs reading exact 0.0%). 31 new runs, ~2.2 CPU-hours,
~5 min wall-clock at 8 workers.

| $m_{\rm max}$ [M☉] | $\langle m\rangle$ [M☉] | Any IMBH? (n=8) | 95% CI (Wilson) | % BHs>100 (mean) | Mergers (mean) |
|---:|---:|:---:|:---:|---:|---:|
| 20.1 | 11.7 | 0/8 (0%) | 0-32% | 0.00% | 39.1 |
| 22.6 | 12.5 | 3/8 (38%) | 14-69% | 0.05% | 48.9 |
| 25.3 | 13.4 | 4/8 (50%) | 22-79% | 0.06% | 54.0 |
| 28.4 | 14.4 | 6/8 (75%) | 41-93% | 0.11% | 62.1 |
| 31.8 | 15.5 | 6/8 (75%) | 41-93% | 0.21% | 78.9 |

Raw per-seed data: `results/phase4b_raw/summary.csv`; combined with pass 1's matching rows
at `results/phase4_raw/summary_combined_star_only_refined.csv`.

**The corrected picture**: this is not a step function. The probability that *any* BH out of
1000 crosses 100 M☉ in a single 10 Gyr trial rises smoothly and continuously from 0% to 75%
across this band — and even at $m_{\rm max}=31.8\,M_\odot$, where pass 1's thin 3/3 sample
looked fully saturated, 2 of the 8 new seeds produce *zero* IMBHs. The 95% confidence
intervals (Wilson score, appropriate for small-$n$ binomial proportions) overlap substantially
between adjacent grid points — e.g. 22.6's [14, 69]% overlaps 25.3's [22, 79]% and 28.4's
[41, 93]% — so this data does not support naming a precise crossing point tighter than "the
onset sits somewhere in roughly 20-32 M☉, with the 50%-probability point closer to
23-26 M☉ than to either edge." Pinning it more precisely than that would need substantially
more seeds per point (rough guide: halving a Wilson CI's width needs roughly a 4x increase in
$n$) — not attempted here, since the qualitative answer below doesn't need it.

**This directly answers the sharper of N26's own two framings of the open question** (Section
5.4: "whether there is a mass distribution between our lower and upper limits that
consistently produces IMBHs" — and, per this project's own framing in `PROJECT_OVERVIEW.md`,
whether any such transition is *sharp* or *gradual*). Under `star_only`, the answer is now
directly evidenced rather than assumed: **gradual, not sharp** — there is a real crossover
region, not a discrete on/off boundary, and it has not even fully saturated to "always forms"
by $m_{\rm max}=31.8\,M_\odot$, less than a third of the way to H18's own 100 $M_\odot$. Whether
pass 1's apparently-saturated 3/3 points further out (63-100 M☉) are genuinely deterministic or
merely under-sampled in the same way was not re-tested here (out of scope for this targeted
pass) and is flagged as an open follow-up, not assumed either way.

## Pass 3: primordial-binary fraction has no detectable effect on the crossover (2026-07-28)

Run 2026-07-28, `scripts/phase4c_primordial_binary_check.py`. Follow-up to the deferral in
`paper/limitations.md#phase4-mass-family-scan`'s original design ("primordial-binary-merger
fraction... deferred to a follow-up, zoomed-in second pass near wherever the first pass finds
a threshold"): does N26's own 15% primordial-binary-merger prescription (Section 3, the "+M"
variants) shift the `star_only` crossover pass 2 located? `star_only` only (`bh_inclusive`'s
absence-of-threshold finding is already saturated evidence and orthogonal to this axis — see
"Analysis" below). Same 5 $m_{\rm max}$ grid points as pass 2, 8 seeds each (0-7),
`primordial_binary_fraction=0.15` vs pass 2's existing `=0.0` runs at identical $m_{\rm max}$.
40 new runs, ~4.9 CPU-hours (avg. ~450s/run, slower than pass 2's ~430s average — consistent
with primordial mergers giving a small fraction of the population a head start into the
runaway-growth regime), ~13 min wall-clock at 8 workers.

Required a small code extension: `initial_conditions.get_log_uniform_samplers` gained a
`primordial_binary_fraction` parameter (default 0.0, backward-compatible with pass 1/2's
calls), applying the same `apply_primordial_mergers` machinery already used for
`sample_k20_plus_m`/`sample_h18_plus_m`. The +M-modified mean has no closed form (mergers are
a nonlinear transform of the base draw), so `mean_bh_mass` is Monte-Carlo-estimated per grid
point ($N=2\times10^6$) at run time.

| $m_{\rm max}$ [M☉] | 0% any (n=8) | 0% CI | 15% any (n=8) | 15% CI | 0% % BHs>100 | 15% % BHs>100 | 0% mergers | 15% mergers |
|---:|:---:|:---:|:---:|:---:|---:|---:|---:|---:|
| 20.1 | 0/8 (0%) | 0-32% | 1/8 (12%) | 2-47% | 0.000 | 0.013 | 39.1 | 38.6 |
| 22.6 | 3/8 (38%) | 14-69% | 1/8 (12%) | 2-47% | 0.050 | 0.013 | 48.9 | 47.1 |
| 25.3 | 4/8 (50%) | 22-78% | 4/8 (50%) | 22-78% | 0.062 | 0.075 | 54.0 | 57.2 |
| 28.4 | 6/8 (75%) | 41-93% | 7/8 (88%) | 53-98% | 0.113 | 0.212 | 62.1 | 66.5 |
| 31.8 | 6/8 (75%) | 41-93% | 7/8 (88%) | 53-98% | 0.212 | 0.287 | 78.9 | 81.0 |

**No consistent, statistically distinguishable shift.** Point-by-point, every 15% value sits
inside (or barely outside) the 0% point's own 95% Wilson interval, and the direction isn't even
consistent — 22.6 M☉ goes *down* (38%→12%) while 28.4 and 31.8 M☉ go slightly up (75%→88%).
Pooled across all 5 points (40 runs each), 0% gives 19/40 (47.5%) any-IMBH runs vs 15%'s 20/40
(50.0%) — a Fisher's exact test on the pooled 2x2 table gives $p=1.0$, i.e. no evidence
whatsoever of an aggregate difference. The one clean, unambiguous effect is on mean population
mass itself: `mean_bh_mass` rises by a consistent **+2.3%** at every single grid point (e.g.
11.669→11.935 at $m_{\rm max}=20.1$, 15.474→15.828 at $m_{\rm max}=31.8$) — matching, almost
exactly, the +2.2% (K20→K20+M) and +2.4% (H18→H18+M) shifts Phase 3 measured for the real
IC pairs (`scripts/phase3_validation.py`'s `MEAN_BH_MASS` dict), a good Gate 6 consistency
check that the new sampler extension is behaving the same way the validated K20+M/H18+M path
does.

**Per `paper/methodology.md`'s gates**: this graduates as a result, not just an observation.
Gate 1 — labeled explicitly as our own combination (N26 states the 15% prescription, Section
3, but never combines it with a scanned mass family; that pairing is ours). Gate 2 — the
claimed "no effect" is checked against the same Wilson-CI noise floor pass 2 used, and the
15% values fall inside it at every point. Gate 4 — mechanism: primordial mergers only touch
2.5% of the population directly (15% paired × 1/3 merged) and raise the mean mass by ~2%,
whereas one step of the $m_{\rm max}$ grid is a ~12% *multiplicative* change in the mass
scale — a far larger perturbation to the same growth-rate-controlling parameter, so a much
weaker effect from this axis is physically expected, not just a null result taken at face
value. Gate 5 — the aggregate Fisher test is itself the falsification check: if there were a
real, if small, effect being masked by point-by-point noise, pooling would surface it; it
didn't ($p=1.0$). This is a genuine **absence-of-effect finding at this resolution**, not
"we didn't look hard enough" — but see Caveats for the honest limit of what 8 seeds/point can
rule out.

## Analysis

**Under `star_only`** (the Phase 3 default), % BHs > 100 M☉ rises roughly monotonically from
0% to 12.7% as $m_{\rm max}$ goes 16→100 M☉, with no obvious discontinuity in that continuous
statistic. The stricter **binary** question ("does even one BH cross 100 M☉, ever, across 1000
BHs × 10 Gyr") is where the interesting structure lives — see "Pass 2" above for the
refined, properly-sampled answer: a genuine, gradual crossover spanning at least
$m_{\rm max}\approx20$-$32\,M_\odot$ (mean population mass $\approx12$-$15\,M_\odot$), not a
sharp step, and not yet fully saturated even at the top of that range — well below H18's own
100 M☉ upper limit either way, i.e. under `star_only` the onset of IMBH formation is much
closer to K20's mass regime than to H18's.

**Under `bh_inclusive`**, no threshold is found anywhere in the tested range. % BHs > 100 M☉
is a flat, exact 0.0% for all 8 grid points from 16 to 79.5 M☉, and even at $m_{\rm max}=100$
(H18 exactly) only reaches a marginal 0.1-0.3% (a literal handful of BHs, barely over the line,
in 2 of 3 seeds) — compare Table 1's actual H18 value of 7.8%, itself only reproduced under
`star_only`. Mergers stay at order-unity counts (~1-2 per run) throughout the whole grid,
consistent with the `#phase2-emri-rate-high` finding that strong relaxation under this reading
evicts BHs into EMRI before either growth channel can operate. IMBH formation under this
reading looks essentially suppressed across the entire physically-motivated mass range N26
considers, not just reduced.

**Revised understanding of "bulk vs. tail" sensitivity to the Eq. 22 ambiguity** (updates the
closing recommendation of `paper/limitations.md#phase2-emri-rate-high`): that entry hypothesized
bulk-population statistics (merger count order of magnitude, % > 100 M☉) would be much less
sensitive to the star-only/bh-inclusive choice than the extreme max-mass tail, based on a single
comparison point (H18, star-only vs bh-inclusive: 12.5% vs 68.8% EMRI, but both mergers-active
vs mergers-zero). This scan shows that hypothesis does **not** hold for the IMBH-formation
question specifically: "% BHs > 100 M☉" itself — not just the single most massive BH — swings
from a clear, gradually-developing signal (0% → 12.7%) under `star_only` to essentially flat
zero under `bh_inclusive`, across the *entire* scanned range. The reason is structural, not
incidental: forming an IMBH via either channel (successive collisions or GW capture) requires a
BH to survive long enough in the dense inner region to grow, and survival time against EMRI
ejection is exactly the timescale this ambiguity controls. So "does an IMBH form at all" is
about as sensitive to this choice as it's possible to be — this is a stronger, structural
finding than the original tail-vs-bulk framing suggested, not a minor refinement of it.

## Caveats

- **Even 8 seeds per point (pass 2) only pins the crossover to a broad range, not a precise
  number.** Wilson CIs overlap substantially between adjacent grid points 22.6-31.8 M☉ — the
  data supports "onset somewhere in ~20-32 M☉, 50%-point closer to 23-26 M☉" but not a tighter
  claim than that. This is a real, quantified limitation, not an oversight: see "Pass 2" above
  for the CI table and the rough $n$-scaling needed to sharpen it further.
- **Whether the apparently-saturated pass-1 points (63-100 M☉, all 3/3 seeds) are genuinely
  deterministic or merely under-sampled the same way $m_{\rm max}=31.8$ turned out to be was
  not re-tested.** Flagged as an open follow-up, not assumed either way — pass 2 deliberately
  scoped its extra seeds to the 20-32 M☉ band where pass 1's signal was weak, not the whole grid.
- **`bh_inclusive`'s "no threshold found" is a statement about the tested range, not a proof of
  absence.** It's possible a threshold exists above $m_{\rm max}=100$ (outside N26's own
  studied range for any initial condition) — not pursued here since it would depart from the
  paper's tested mass regime entirely, but flagged as a logical possibility rather than a hard
  boundary.
- **This mass family is an approximation of K20 at its low end, not an exact reproduction** —
  see `paper/limitations.md#phase4-mass-family-scan`. The $m_{\rm max}=16$ point's 0%
  result is consistent with, but not identical to, actual K20's exact 0% (Phase 3, 6/6 seeds
  across K20+K20+M).
- **Pass 3's "no detectable effect" is bounded by the same 8-seed resolution as pass 2's
  location claim** — it rules out an effect large enough to clear that noise floor, not an
  arbitrarily small one. A genuinely small shift (say, a few percentage points in the
  any-IMBH probability, comparable in size to the mean-mass bump's own ~2.3% scale) could
  exist and still be invisible at $n=8$/point; Gate 3's own rough scaling (halving a Wilson
  CI needs ~4x the seeds) means ruling that out with confidence would need on the order of
  32 seeds/point, not attempted here since the pooled Fisher test ($p=1.0$) gave no
  directional hint worth chasing at that cost.
- **Only `star_only` was checked for this axis.** Whether primordial-binary fraction shifts
  anything under `bh_inclusive` is untested — deliberately out of scope, since that reading's
  own threshold question is already closed (no threshold anywhere in the tested mass range,
  regardless of this axis being untested there).

## Bottom line

Phase 4's central question — is there a sharp critical initial-mass-distribution threshold for
IMBH formation, or a gradual one? — now has a genuine, evidenced answer, still *conditional* on
the still-open Eq. 22 ambiguity: under `star_only`, IMBH formation onset is **gradual, not
sharp** — a real crossover region spanning at least 20-32 M☉ (mean population mass
12-15 M☉), well below H18's own upper mass limit, that has not even fully saturated by the top
of that range; under `bh_inclusive`, the picture is closer to "IMBHs essentially don't form
dynamically anywhere in N26's studied mass range," full stop, with no crossover to locate.
**Any claim about "where the threshold is" (or whether it's even sharp) must specify which
reading of Eq. 22 it assumes** — this is not a detail that washes out at the bulk-population
level, as hoped going into Phase 4.

Pass 3 adds one more piece: **the mass-scale axis ($m_{\rm max}$) is what drives the crossover,
not the primordial-binary-merger fraction.** N26's own 0%/15% axis, tested at the same
resolution that located the crossover in the first place, produces no distinguishable shift
(pooled $p=1.0$) — consistent with the mechanism identified for the crossover itself (survival
time against EMRI ejection, gated by the population's overall mass/density, not by whether 2.5%
of it started out pre-merged). This completes the scope originally planned for Phase 4 at
design time (both Eq. 22 readings, the threshold's existence and shape, and the deferred
primordial-fraction axis); further refinement (more seeds at the already-saturated 63-100 M☉
end, or extending `bh_inclusive` past $m_{\rm max}=100$) is possible but judged lower-value —
see Caveats for what's left open and why it wasn't chased further here.
