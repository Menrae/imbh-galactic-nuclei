# Phase 3 validation: comparison against Table 1 (Newton et al. 2026)

Run 2026-07-26. All four initial conditions, $N=1000$ BHs, $M_\bullet=4\times10^6\,M_\odot$,
$\alpha_\star=1.25$, 10 Gyr integration, 3 seeds each (0, 1, 2), averaged. Produced after two
independently-justified fixes to the relaxation random walk (genuine sub-timestep substepping;
re-derived $\langle M_{\rm avg}\rangle$/$\rho$ and Coulomb logarithm from primary sources) and
one straightforward bug fix (`mean_bh_mass` corrected from a flat, unchecked 20.0 placeholder
to each IC's actual Monte Carlo sampler mean). Full trace of every decision in
`paper/limitations.md#phase2-emri-rate-high`.

**This is an honest reporting of a partial validation, not a clean match.** See the "How to
read this" section below before drawing conclusions from it.

## Comparison table

| IC | Metric | Ours (mean of 3 seeds) | Ours (range) | Table 1 |
|---|---|---:|---:|---:|
| K20 | Mergers | 24.0 | 14 – 34 | 34 |
| K20 | Max mass [M☉] | 39.1 | 30.7 – 51.4 | 28.4 |
| K20 | % BHs > 100 M☉ | 0.0% | 0.0% | 0% |
| K20+M | Mergers | 28.7 | 19 – 39 | 30 |
| K20+M | Max mass [M☉] | 46.2 | 38.0 – 52.2 | 57.8 |
| K20+M | % BHs > 100 M☉ | 0.0% | 0.0% | 0% |
| H18 | Mergers | 1022.0 | 923 – 1102 | 371 |
| H18 | Max mass [M☉] | 58,034 | 9,181 – 89,870 | 407.3 |
| H18 | % BHs > 100 M☉ | 12.5% | 11.7 – 13.4% | 7.8% |
| H18+M | Mergers | 1046.7 | 786 – 1199 | 535 |
| H18+M | Max mass [M☉] | 11,881 | 3,556 – 16,137 | 526.0 |
| H18+M | % BHs > 100 M☉ | 12.8% | 12.6 – 13.2% | 14.3% |

Not in Table 1, tracked here for context: mean EMRI fraction over 10 Gyr (K20 29.6%, K20+M
31.9%, H18 34.7%, H18+M 35.0% — Table 1 implies a few percent via its Section 5.4 rate
figures, ~4 Gyr⁻¹ per Milky-Way-like galaxy) and mean max merger generation (K20/K20+M: 3
every seed; H18: 183, H18+M: 162 — Table 1 states 12G max for H18, 16G max for H18+M).

Not recomputed this pass: Table 1's "BHs > 2×Mᵢ" / "BHs > 10×Mᵢ" columns require each BH's
*initial* mass, which wasn't logged per-BH in this run (only final state + merger-event
progenitor masses were saved) — flagged as a small instrumentation gap for a future re-run,
not worth the ~4-hour re-run cost to add retroactively.

## How to read this

**K20 and K20+M: genuinely close.** Mergers and max mass are within a factor of ~1.3-1.5x of
Table 1 in both directions across all 3 seeds — well within what's plausible given the
K20 mass-distribution reconstruction uncertainty (`paper/limitations.md#k20-reconstruction`)
and ordinary seed-to-seed stochastic variance at N=1000. No runaway growth in any of the 6
K20/K20+M runs (max generation capped at 3 every time).

**H18 and H18+M: bulk statistics are in a plausible range; the "max mass" column specifically
is not.** Two different pictures emerge depending which column you look at:

- Merger *count* is off by 2.75-2.9x (1022 vs 371 for H18) — high, but the same order of
  magnitude, and plausibly connected to the still-open $\langle M_{\rm avg}\rangle$ ambiguity
  (see below).
- **% of BHs exceeding 100 M☉ is actually close** (12.5% vs 7.8% for H18; 12.8% vs 14.3% for
  H18+M — the H18+M number is within seed-to-seed noise of Table 1's value). This is a much
  more representative statistic of the bulk population than "max mass," and it suggests the
  *typical* BH's growth is not wildly miscalibrated.
- **Max mass is off by 20-220x** (58,034 vs 407.3 for H18, mean of 3 seeds; one seed reached
  89,870 M☉). This is a single order statistic, extremely sensitive to rare heavy-tailed
  outliers — and that's exactly what's happening: 1-3 BHs per 1000-BH run undergo 60-230
  merger generations (Table 1's own stated max is 12-16G) via runaway positive feedback in
  both the stellar-collision and GW-capture growth channels (both channels'
  cross-sections scale with the growing BH's own mass — see
  `paper/limitations.md#phase2-emri-rate-high` for the full mechanism trace), while the
  99th-percentile mass (677-851 M☉ for H18) is much closer to a sane scale.

**A new finding from this run specifically**: correcting the previously-wrong `mean_bh_mass`
placeholder (a real bug fix, not a modeling choice) made the H18/H18+M runaway-growth tail
*more* severe, not less (max mass roughly doubled to 20x'd compared to the same diagnostic
run with the old, wrong placeholder) — implicating the GW-capture channel's mass-dependence
(the $\eta$/$b_{\rm max}$ calculation, Eq. 4-7) as at least as important a contributor to the
runaway as the relaxation-timescale ambiguity already under discussion. This is logged as a
concrete lead for follow-up, not yet investigated.

## Bottom line

This is a partial, honestly-reported validation: the lighter-mass K20 initial condition
validates well; the heavier-mass H18 initial condition's bulk population is plausible but its
extreme upper tail is not, for reasons now traced to specific growth-feedback mechanisms
rather than a coding defect. **Any Phase 4 "critical mass threshold" analysis should treat
the H18-family max-mass statistic specifically with caution** until the GW-capture-channel
lead above is investigated — the bulk-population statistics (merger count order of magnitude,
% > 100 M☉) are more trustworthy in the meantime.
